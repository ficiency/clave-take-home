'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Send } from 'lucide-react'

export function ChatInput() {
  const [message, setMessage] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!message.trim()) return
    
    console.log('Message:', message)
    setMessage('')
  }

  return (
    <div className="flex flex-col items-center justify-center gap-4">
      <p className="text-muted-foreground">
        Hello, how can I help you today?
      </p>
      <form
        onSubmit={handleSubmit}
        className="flex w-full max-w-2xl items-center gap-2"
      >
        <Input
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Ask anything..."
          className="flex-1"
        />
        <Button type="submit" size="icon" disabled={!message.trim()}>
          <Send className="h-4 w-4" />
        </Button>
      </form>
    </div>
  )
}

