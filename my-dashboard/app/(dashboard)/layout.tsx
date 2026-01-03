'use client'

import { useState, useEffect } from 'react'
import { usePathname, useRouter } from 'next/navigation'
import { Sidebar } from '@/app/_components/layout/Sidebar'
import { getAuthToken } from '@/app/_lib/client-auth'

interface Conversation {
  conversation_id: string
  title: string
  created_at: string
  updated_at: string
}

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)
  const [conversations, setConversations] = useState<Array<{ id: string; title: string }>>([])
  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(null)
  const router = useRouter()
  const pathname = usePathname()

  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen)
  }

  useEffect(() => {
    const loadConversations = async () => {
      const token = getAuthToken()
      if (!token) return

      try {
        const response = await fetch('/api/conversations', {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        })

        if (response.ok) {
          const { conversations: convs } = await response.json()
          setConversations(convs.map((c: Conversation) => ({
            id: c.conversation_id,
            title: c.title,
          })))
        }
      } catch (error) {
        console.error('Error loading conversations:', error)
      }
    }

    loadConversations()
  }, [])

  const handleSelectConversation = (conversationId: string) => {
    setSelectedConversationId(conversationId)
    router.push(`/chat?conversation=${conversationId}`)
  }

  const handleNewChat = () => {
    setSelectedConversationId(null)
    router.push('/chat')
  }

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar 
        isOpen={isSidebarOpen} 
        onToggle={toggleSidebar}
        conversations={conversations}
        selectedConversationId={selectedConversationId}
        onSelectConversation={handleSelectConversation}
        onNewChat={handleNewChat}
      />
      <main className="flex-1 overflow-y-auto">{children}</main>
    </div>
  )
}

