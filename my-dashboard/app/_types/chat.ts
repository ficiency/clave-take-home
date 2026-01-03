import { ChartConfig } from './chart'

export interface Message {
  id: string
  role: 'user' | 'ai'
  content: string
  metadata?: {
    sql?: string
    chart?: ChartConfig
  }
  created_at?: string
}

export interface Conversation {
  id: string
  title: string
  created_at: string
  updated_at: string
}

export type StreamEvent =
  | { type: 'text'; content: string }
  | { type: 'sql'; content: string }
  | { type: 'chart'; content: ChartConfig }
  | { type: 'done' }
  | { type: 'error'; content: string }

