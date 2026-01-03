import { NextRequest, NextResponse } from 'next/server'
import { getSupabaseAdmin } from '@/app/_lib/supabase/server'
import { getAccountIdFromRequest } from '@/app/_lib/auth'

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ conversationId: string }> }
) {
  try {
    const accountId = getAccountIdFromRequest(request)
    
    if (!accountId) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      )
    }

    const { conversationId } = await params

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

    // Get messages
    const { data: messages, error } = await supabaseAdmin
      .from('messages')
      .select('message_id, role, content, created_at')
      .eq('conversation_id', conversationId)
      .order('created_at', { ascending: true })

    if (error) {
      console.error('Error fetching messages:', error)
      return NextResponse.json(
        { error: 'Failed to fetch messages' },
        { status: 500 }
      )
    }

    return NextResponse.json({ messages: messages || [] }, { status: 200 })
  } catch (error) {
    console.error('Get messages error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}

