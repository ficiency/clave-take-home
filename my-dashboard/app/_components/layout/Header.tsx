'use client'

import { SidebarToggle } from './SidebarToggle'

interface HeaderProps {
  isSidebarOpen: boolean
  onToggleSidebar: () => void
}

export function Header({ isSidebarOpen, onToggleSidebar }: HeaderProps) {
  return (
    <header className="flex h-14 items-center border-b px-4">
      <SidebarToggle onClick={onToggleSidebar} isOpen={isSidebarOpen} />
    </header>
  )
}

