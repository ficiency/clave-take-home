'use client'

import { Button } from '@/components/ui/button'
import { Menu } from 'lucide-react'

interface SidebarToggleProps {
  onClick: () => void
  isOpen: boolean
}

export function SidebarToggle({ onClick, isOpen }: SidebarToggleProps) {
  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={onClick}
      className="h-9 w-9"
    >
      <Menu className="h-5 w-5" />
    </Button>
  )
}

