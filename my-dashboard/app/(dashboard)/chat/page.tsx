'use client'

import { Suspense } from 'react'
import { ChatInput } from '@/app/_components/chat/ChatInput'
import { useSearchParams } from 'next/navigation'

function ChatContent() {
  const searchParams = useSearchParams()
  const conversationId = searchParams.get('conversation')

  return (
    <div className="flex h-full flex-col">
      <ChatInput conversationId={conversationId} />
    </div>
  )
}

export default function ChatPage() {
  return (
    <Suspense fallback={<div className="flex h-full flex-col" />}>
      <ChatContent />
    </Suspense>
  )
}
