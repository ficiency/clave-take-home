'use client'

import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { PanelLeft, PenSquare } from 'lucide-react'
import { cn } from '@/lib/utils'

interface SidebarProps {
  isOpen: boolean
  onToggle: () => void
  conversations?: Array<{ id: string; title: string }>
}

export function Sidebar({ isOpen, onToggle, conversations = [] }: SidebarProps) {
  return (
    <aside
      className={cn(
        'flex flex-col border-r bg-background transition-all duration-300',
        isOpen ? 'w-64' : 'w-12'
      )}
    >
      <div className={cn(
        'flex flex-col',
        !isOpen ? 'items-center p-2' : 'py-2'
      )}>
        <div className={cn(
          'flex items-center',
          isOpen ? 'justify-between px-3' : 'justify-center'
        )}>
          {isOpen && (
            <img 
              src="/logo.svg" 
              alt="Logo" 
              className="h-6 w-6"
            />
          )}
          <Button
            variant="ghost"
            size="icon"
            onClick={onToggle}
            className={cn(
              'h-9 w-9',
              !isOpen && 'mx-auto'
            )}
          >
            <PanelLeft className="h-5 w-5" />
          </Button>
        </div>
        
        <Separator className="my-2 w-full" />
        
        <div className={cn(
          !isOpen && 'flex justify-center'
        )}>
          <Button
            variant="ghost"
            size="icon"
            className={cn(
              'h-9 w-9',
              isOpen && 'w-full justify-start gap-2 px-3'
            )}
          >
            <PenSquare className="h-5 w-5 shrink-0" />
            {isOpen && <span className="text-sm">New chat</span>}
          </Button>
        </div>
      </div>

      {isOpen && (
        <>
          <Separator className="my-2" />
          <div className="flex-1 overflow-y-auto">
            <div className="space-y-1 px-2">
              {conversations.length === 0 ? (
                <p className="px-3 py-2 text-sm text-muted-foreground">
                  No conversations yet
                </p>
              ) : (
                conversations.map((conversation) => (
                  <Button
                    key={conversation.id}
                    variant="ghost"
                    className="w-full justify-start text-left"
                  >
                    <span className="truncate text-sm">
                      {conversation.title}
                    </span>
                  </Button>
                ))
              )}
            </div>
          </div>
        </>
      )}
    </aside>
  )
}

