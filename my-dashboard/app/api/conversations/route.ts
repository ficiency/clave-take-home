import { NextRequest, NextResponse } from 'next/server'
import { getSupabaseAdmin } from '@/app/_lib/supabase/server'
import { getAccountIdFromRequest } from '@/app/_lib/auth'

export async function GET(request: NextRequest) {
  try {
    const accountId = getAccountIdFromRequest(request)
    
    if (!accountId) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      )
    }

    const supabaseAdmin = getSupabaseAdmin()

    const { data: conversations, error } = await supabaseAdmin
      .from('conversations')
      .select('conversation_id, title, created_at, updated_at')
      .eq('account_id', accountId)
      .order('updated_at', { ascending: false })

    if (error) {
      console.error('Error fetching conversations:', error)
      return NextResponse.json(
        { error: 'Failed to fetch conversations' },
        { status: 500 }
      )
    }

    return NextResponse.json({ conversations: conversations || [] }, { status: 200 })
  } catch (error) {
    console.error('Conversations error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}

export async function POST(request: NextRequest) {
  try {
    const accountId = getAccountIdFromRequest(request)
    
    if (!accountId) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      )
    }

    const { title } = await request.json()
    
    const supabaseAdmin = getSupabaseAdmin()

    const { data: conversation, error } = await supabaseAdmin
      .from('conversations')
      .insert({
        account_id: accountId,
        title: title || 'New Conversation',
      })
      .select('conversation_id, title, created_at, updated_at')
      .single()

    if (error) {
      console.error('Error creating conversation:', error)
      return NextResponse.json(
        { error: 'Failed to create conversation' },
        { status: 500 }
      )
    }

    return NextResponse.json({ conversation }, { status: 201 })
  } catch (error) {
    console.error('Create conversation error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}

