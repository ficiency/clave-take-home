import { NextRequest } from 'next/server'
import { getAccountIdFromRequest } from '@/app/_lib/auth'
import { getSupabaseAdmin } from '@/app/_lib/supabase/server'
import { ChatOpenAI } from '@langchain/openai'
import { HumanMessage, AIMessage, ToolMessage, AIMessageChunk } from '@langchain/core/messages'
import { createAgent } from 'langchain'
import { SYSTEM_PROMPT } from '@/app/_lib/agent/prompts'
import { createExecuteSQLTool, createChartTool } from '@/app/_lib/agent/tools'
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

    // 5. Obtener últimos 5 mensajes para contexto (incluye el que acabamos de guardar)
    // Ordenados por fecha descendente para luego revertir
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

    // 6. Inicializar modelo y crear agente con tools
    const model = new ChatOpenAI({
      modelName: 'gpt-5.2',
      streaming: true,
      temperature: 0.3,
    })

    const tools = [createExecuteSQLTool(), createChartTool()]

    const agent = createAgent({
      model,
      tools,
      systemPrompt: SYSTEM_PROMPT,
    })

    // 7. Crear ReadableStream para SSE
    const stream = new ReadableStream({
      async start(controller) {
        const encoder = new TextEncoder()
        let fullResponse = ''
        let chartConfig: any = null
        let previousWasChunk = false // Rastrear si el mensaje anterior era un chunk

        const sendEvent = (event: StreamEvent) => {
          const data = JSON.stringify(event)
          controller.enqueue(encoder.encode(`data: ${data}\n\n`))
        }

        try {
          console.log('[AI REQUEST] Flag crossed - Starting agent stream')
          
          // Stream del agente
          const responseStream = await agent.stream({
            messages: langchainMessages,
          }, {
            streamMode: 'updates',
          })

          let processedContent = new Set<string>() // Rastrear contenido ya procesado
          
          for await (const updates of responseStream) {
            console.log(`[STREAM] Update received for node: ${Object.keys(updates).join(', ')}`)
            for (const [nodeName, nodeUpdate] of Object.entries(updates)) {
              if (nodeUpdate.messages && Array.isArray(nodeUpdate.messages)) {
                console.log(`[STREAM] Node "${nodeName}" has ${nodeUpdate.messages.length} messages`)
                
                // Solo procesar el ÚLTIMO mensaje de cada tipo para evitar duplicados
                const lastMessage = nodeUpdate.messages[nodeUpdate.messages.length - 1]
                
                // Crear un ID único para este mensaje basado en su contenido y tipo
                const messageId = `${nodeName}-${lastMessage.constructor.name}-${JSON.stringify(lastMessage.content).substring(0, 100)}`
                
                if (processedContent.has(messageId)) {
                  console.log(`[STREAM] Message already processed, skipping`)
                  continue
                }
                
                processedContent.add(messageId)
                console.log(`[STREAM] Message type: ${lastMessage.constructor.name}`)
                
                if (lastMessage instanceof ToolMessage) {
                  console.log(`[STREAM] ToolMessage from tool: ${lastMessage.name}`)
                  // Detectar si es resultado de create_chart
                  try {
                    const toolContent = typeof lastMessage.content === 'string' 
                      ? lastMessage.content 
                      : String(lastMessage.content)
                    const toolResult = JSON.parse(toolContent)
                    if (toolResult.success && toolResult.chart) {
                      chartConfig = toolResult.chart
                      sendEvent({ type: 'chart', content: toolResult.chart })
                    }
                  } catch (e) {
                    // No es JSON válido o no es chart, continuar
                  }
                  continue
                }
                
                // Manejar tanto AIMessage como AIMessageChunk
                if (lastMessage instanceof AIMessage || lastMessage instanceof AIMessageChunk) {
                  const content = lastMessage.content
                  const hasToolCalls = lastMessage.tool_calls && lastMessage.tool_calls.length > 0
                  
                  console.log(`[STREAM] ${lastMessage instanceof AIMessageChunk ? 'AIMessageChunk' : 'AIMessage'} - hasToolCalls: ${hasToolCalls}, content: "${content}", contentType: ${typeof content}`)
                  
                  // Streamear contenido de texto SIEMPRE, incluso si hay tool_calls
                  if (content) {
                    const contentStr = typeof content === 'string' ? content : String(content)
                    if (contentStr.trim()) {
                      // Agregar 2 saltos de línea antes de cada chunk nuevo si el anterior también era chunk
                      const textToStream = lastMessage instanceof AIMessageChunk && previousWasChunk
                        ? `\n\n${contentStr}` 
                        : contentStr
                      
                      console.log(`[STREAM] Streaming text content: "${contentStr.substring(0, 50)}..."`)
                      fullResponse += textToStream
                      sendEvent({ type: 'text', content: textToStream })
                      
                      // Actualizar flag para el próximo mensaje
                      previousWasChunk = lastMessage instanceof AIMessageChunk
                    } else {
                      console.log(`[STREAM] Content is empty string`)
                    }
                  } else {
                    console.log(`[STREAM] Content is null/undefined`)
                  }
                  
                  if (hasToolCalls && lastMessage.tool_calls) {
                    console.log(`[STREAM] Tool calls detected:`, lastMessage.tool_calls.map((tc: any) => tc.name))
                  }
                }
              }
            }
          }

          // Guardar respuesta completa en DB con metadata
          const messageMetadata = chartConfig ? { chart: chartConfig } : {}
          console.log('[CHAT] Saving message with metadata:', JSON.stringify(messageMetadata, null, 2))
          
          await supabaseAdmin.from('messages').insert({
            conversation_id: conversationId,
            role: 'ai',
            content: fullResponse,
            metadata: messageMetadata,
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

