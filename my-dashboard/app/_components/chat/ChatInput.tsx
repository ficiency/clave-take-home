'use client'

import { useState, useRef, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { UserMessage } from './UserMessage'
import { AIMessage } from './AIMessage'
import { getAuthToken } from '@/app/_lib/client-auth'

interface Message {
  id: string
  role: 'user' | 'ai'
  content: string
}

interface ChatInputProps {
  conversationId?: string | null
}

export function ChatInput({ conversationId: propConversationId }: ChatInputProps) {
  const [message, setMessage] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [conversationId, setConversationId] = useState<string | null>(propConversationId || null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Load messages when conversationId changes
  useEffect(() => {
    if (propConversationId) {
      setConversationId(propConversationId)
      loadMessages(propConversationId)
    } else {
      setConversationId(null)
      setMessages([])
    }
  }, [propConversationId])

  const loadMessages = async (convId: string) => {
    const token = getAuthToken()
    if (!token) return

    try {
      const response = await fetch(`/api/conversations/${convId}/messages`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (response.ok) {
        const { messages: loadedMessages } = await response.json()
        setMessages(loadedMessages.map((msg: any) => ({
          id: msg.message_id,
          role: msg.role,
          content: msg.content,
        })))
      }
    } catch (error) {
      console.error('Error loading messages:', error)
    }
  }

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`
    }
  }, [message])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!message.trim()) return
    
    const token = getAuthToken()
    if (!token) {
      console.error('No auth token found')
      return
    }

    const userMessageContent = message.trim()
    setMessage('')

    // Create conversation if this is the first message
    let currentConversationId = conversationId
    if (!currentConversationId) {
      try {
        const convResponse = await fetch('/api/conversations', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify({ title: userMessageContent.slice(0, 50) }),
        })

        if (!convResponse.ok) {
          console.error('Failed to create conversation')
          return
        }

        const { conversation } = await convResponse.json()
        currentConversationId = conversation.conversation_id
        setConversationId(currentConversationId)
      } catch (error) {
        console.error('Error creating conversation:', error)
        return
      }
    }

    // Save user message
    try {
      const userMsgResponse = await fetch('/api/messages', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          conversationId: currentConversationId,
          role: 'user',
          content: userMessageContent,
        }),
      })

      if (!userMsgResponse.ok) {
        console.error('Failed to save user message')
      } else {
        const { message: savedMsg } = await userMsgResponse.json()
        setMessages((prev) => [...prev, {
          id: savedMsg.message_id,
          role: 'user',
          content: savedMsg.content,
        }])
      }
    } catch (error) {
      console.error('Error saving user message:', error)
    }

    // Simulate AI response (temporary)
    setTimeout(async () => {
      const aiResponseContent = 'This is a simulated AI response. The actual AI integration will be implemented later.'
      
      try {
        const aiMsgResponse = await fetch('/api/messages', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify({
            conversationId: currentConversationId,
            role: 'ai',
            content: aiResponseContent,
          }),
        })

        if (!aiMsgResponse.ok) {
          console.error('Failed to save AI message')
        } else {
          const { message: savedMsg } = await aiMsgResponse.json()
          setMessages((prev) => [...prev, {
            id: savedMsg.message_id,
            role: 'ai',
            content: savedMsg.content,
          }])
        }
      } catch (error) {
        console.error('Error saving AI message:', error)
      }
    }, 500)
  }

  const hasMessages = messages.length > 0

  return (
    <div className="flex w-full flex-col h-full">
      {!hasMessages && (
        <div className="flex flex-1 flex-col items-center justify-center gap-4 px-4">
          <p className="flex items-baseline gap-2 text-3xl">
            <img 
              src="/logo.svg" 
              alt="Logo" 
              className="h-8 w-8 shrink-0"
            />
            <span>
              <span className="font-borel">hello Clave Team!</span>
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
      )}
      
      {hasMessages && (
        <>
          <div className="flex-1 overflow-y-auto px-4 py-4">
            <div className="w-full max-w-2xl mx-auto space-y-4">
              {messages.map((msg) => (
                msg.role === 'user' ? (
                  <UserMessage key={msg.id} content={msg.content} />
                ) : (
                  <AIMessage key={msg.id} content={msg.content} />
                )
              ))}
              <div ref={messagesEndRef} />
            </div>
          </div>

          <div className="sticky bottom-0 bg-background border-t pt-4 pb-4 px-4">
            <form
              onSubmit={handleSubmit}
              className="w-full max-w-2xl mx-auto"
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
        </>
      )}
    </div>
  )
}

