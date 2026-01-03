'use client'

import { useState, useRef, useEffect } from 'react'
import { Button } from '@/components/ui/button'

export function ChatInput() {
  const [message, setMessage] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`
    }
  }, [message])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!message.trim()) return
    
    console.log('Message:', message)
    setMessage('')
  }

  return (
    <div className="flex w-full flex-col items-center justify-center gap-4 px-4">
      <p className="flex items-baseline gap-2 text-3xl">
        <img 
          src="/logo.svg" 
          alt="Logo" 
          className="h-8 w-8 shrink-0"
        />
        <span>
          <span className="font-borel">hello!</span>
        </span>
      </p>
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-2xl"
      >
        <div className="rounded-lg border bg-background p-4 shadow-md">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Ask anything..."
            rows={1}
            className="w-full resize-none border-0 bg-transparent text-sm focus:outline-none focus:ring-0"
            style={{ minHeight: '24px', maxHeight: '200px', overflowY: 'auto' }}
          />
          <div className="flex justify-end pt-2">
            <Button
              type="submit"
              size="icon"
              disabled={!message.trim()}
              className="h-8 w-8 shrink-0 bg-black text-white hover:bg-black/90 disabled:opacity-50"
            >
              <img 
                src="/clave-icon.svg" 
                alt="Send" 
                className="h-4 w-4"
              />
            </Button>
          </div>
        </div>
      </form>
    </div>
  )
}

