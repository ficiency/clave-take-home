import { NextRequest } from 'next/server'
import { getAccountIdFromRequest } from '@/app/_lib/auth'
import { getSupabaseAdmin } from '@/app/_lib/supabase/server'
import { ChatOpenAI } from '@langchain/openai'
import { HumanMessage, AIMessage } from '@langchain/core/messages'
import { StreamEvent } from '@/app/_types/chat'

export async function POST(request: NextRequest) {
  try {
    // 1. Autenticación
    const accountId = getAccountIdFromRequest(request)
    if (!accountId) {
      return new Response(JSON.stringify({ error: 'Unauthorized' }), {
        status: 401,
        headers: { 'Content-Type': 'application/json' },
      })
    }

    // 2. Parse body
    const { conversationId, message } = await request.json()

    if (!conversationId || !message?.trim()) {
      return new Response(JSON.stringify({ error: 'conversationId and message are required' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' },
      })
    }

    const supabaseAdmin = getSupabaseAdmin()

    // 3. Validar conversación pertenece al account
    const { data: conversation, error: convError } = await supabaseAdmin
      .from('conversations')
      .select('conversation_id')
      .eq('conversation_id', conversationId)
      .eq('account_id', accountId)
      .single()

    if (convError || !conversation) {
      return new Response(JSON.stringify({ error: 'Conversation not found' }), {
        status: 404,
        headers: { 'Content-Type': 'application/json' },
      })
    }

    // 4. Guardar mensaje del usuario
    await supabaseAdmin.from('messages').insert({
      conversation_id: conversationId,
      role: 'user',
      content: message.trim(),
    })

    // 5. Obtener últimos 5 mensajes para contexto (ordenados por fecha ascendente)
    const { data: historyMessages, error: historyError } = await supabaseAdmin
      .from('messages')
      .select('role, content')
      .eq('conversation_id', conversationId)
      .order('created_at', { ascending: false })
      .limit(5)

    if (historyError) {
      console.error('Error fetching message history:', historyError)
    }

    // Convertir a formato LangChain (revertir para tener orden cronológico)
    const langchainMessages = (historyMessages || [])
      .reverse()
      .map((msg) =>
        msg.role === 'user'
          ? new HumanMessage(msg.content)
          : new AIMessage(msg.content)
      )

    // 6. Inicializar modelo con streaming
    const model = new ChatOpenAI({
      modelName: 'gpt-5.2',
      streaming: true,
      temperature: 0.3,
    })

    // 7. Crear ReadableStream para SSE
    const stream = new ReadableStream({
      async start(controller) {
        const encoder = new TextEncoder()
        let fullResponse = ''

        const sendEvent = (event: StreamEvent) => {
          const data = JSON.stringify(event)
          controller.enqueue(encoder.encode(`data: ${data}\n\n`))
        }

        try {
          // Stream de LangChain
          const responseStream = await model.stream(langchainMessages)

          for await (const chunk of responseStream) {
            const chunkContent = chunk.content
            if (chunkContent) {
              const content = typeof chunkContent === 'string' 
                ? chunkContent 
                : String(chunkContent)
              fullResponse += content
              sendEvent({ type: 'text', content })
            }
          }

          // Guardar respuesta completa en DB
          await supabaseAdmin.from('messages').insert({
            conversation_id: conversationId,
            role: 'ai',
            content: fullResponse,
          })

          // Actualizar updated_at de conversación
          await supabaseAdmin
            .from('conversations')
            .update({ updated_at: new Date().toISOString() })
            .eq('conversation_id', conversationId)

          sendEvent({ type: 'done' })
          controller.close()
        } catch (error) {
          console.error('Streaming error:', error)
          sendEvent({
            type: 'error',
            content: error instanceof Error ? error.message : 'Unknown error',
          })
          controller.close()
        }
      },
    })

    // 8. Retornar Response con SSE headers
    return new Response(stream, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    })
  } catch (error) {
    console.error('Chat endpoint error:', error)
    return new Response(
      JSON.stringify({ error: 'Internal server error' }),
      {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      }
    )
  }
}

