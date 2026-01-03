import { NextRequest, NextResponse } from 'next/server'
import { getSupabaseAdmin } from '@/app/_lib/supabase/server'
import { getAccountIdFromRequest } from '@/app/_lib/auth'

export async function POST(request: NextRequest) {
  try {
    const accountId = getAccountIdFromRequest(request)
    
    if (!accountId) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      )
    }

    const { conversationId, role, content } = await request.json()

    if (!conversationId || !role || !content) {
      return NextResponse.json(
        { error: 'conversationId, role, and content are required' },
        { status: 400 }
      )
    }

    if (role !== 'user' && role !== 'ai') {
      return NextResponse.json(
        { error: 'role must be "user" or "ai"' },
        { status: 400 }
      )
    }

    const supabaseAdmin = getSupabaseAdmin()

    // Verify conversation belongs to account
    const { data: conversation, error: convError } = await supabaseAdmin
      .from('conversations')
      .select('conversation_id')
      .eq('conversation_id', conversationId)
      .eq('account_id', accountId)
      .single()

    if (convError || !conversation) {
      return NextResponse.json(
        { error: 'Conversation not found' },
        { status: 404 }
      )
    }

    const { data: message, error } = await supabaseAdmin
      .from('messages')
      .insert({
        conversation_id: conversationId,
        role,
        content,
      })
      .select('message_id, conversation_id, role, content, created_at')
      .single()

    if (error) {
      console.error('Error creating message:', error)
      return NextResponse.json(
        { error: 'Failed to create message' },
        { status: 500 }
      )
    }

    return NextResponse.json({ message }, { status: 201 })
  } catch (error) {
    console.error('Create message error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}

