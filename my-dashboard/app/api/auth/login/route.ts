import { NextRequest, NextResponse } from 'next/server'
import { getSupabaseAdmin } from '@/app/_lib/supabase/server'
import bcrypt from 'bcryptjs'

export async function POST(request: NextRequest) {
  try {
    const { email, password } = await request.json()

    if (!email || !password) {
      return NextResponse.json(
        { error: 'Email and password are required' },
        { status: 400 }
      )
    }

    const supabaseAdmin = getSupabaseAdmin()

    const { data: account, error } = await supabaseAdmin
      .from('accounts')
      .select('account_id, email, password_hash, franchise_name')
      .eq('email', email)
      .single()

    if (error || !account) {
      return NextResponse.json(
        { error: 'Invalid credentials' },
        { status: 401 }
      )
    }

    const isValidPassword = await bcrypt.compare(password, account.password_hash)

    if (!isValidPassword) {
      return NextResponse.json(
        { error: 'Invalid credentials' },
        { status: 401 }
      )
    }

    return NextResponse.json(
      {
        user: {
          id: account.account_id,
          email: account.email,
          franchiseName: account.franchise_name,
        },
        token: account.account_id,
      },
      { status: 200 }
    )
  } catch (error) {
    console.error('Login error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}

