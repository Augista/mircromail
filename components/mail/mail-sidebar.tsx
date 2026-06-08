'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Inbox, Send, FileText, Trash2, Plus, Mail } from 'lucide-react'
import { cn } from '@/lib/utils'
import MailComposer from './mail-composer'

const folders = [
  { icon: Inbox, label: 'Inbox', href: '/mail/inbox', count: 12 },
  { icon: Send, label: 'Sent', href: '/mail/sent', count: 5 },
  { icon: FileText, label: 'Drafts', href: '/mail/drafts', count: 2 },
  { icon: Trash2, label: 'Trash', href: '/mail/trash', count: 0 },
]

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function MailSidebar() {
  const pathname = usePathname()
  const [isComposerOpen, setIsComposerOpen] = useState(false)

  const handleSendEmail = async (email: { to: string; subject: string; body: string }) => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null
    const response = await fetch(`${API_URL}/api/mails`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({
        recipient: email.to,
        subject: email.subject,
        body: email.body,
      }),
    })
    if (!response.ok) {
      const data = await response.json()
      throw new Error(data.detail || 'Failed to send email')
    }
  }

  return (
    <div className="w-64 border-r border-border bg-card p-4 space-y-4">
      <div className="flex items-center gap-2 px-4 py-2">
        <div className="bg-primary p-2 rounded-lg">
          <Mail className="w-5 h-5 text-primary-foreground" />
        </div>
        <span className="font-bold text-lg text-foreground">MicroMail</span>
      </div>

      <Button
        onClick={() => setIsComposerOpen(true)}
        className="w-full"
        size="lg"
      >
        <Plus className="w-4 h-4 mr-2" />
        Compose
      </Button>

      <div className="space-y-1">
        {folders.map((folder) => {
          const Icon = folder.icon
          const isActive = pathname === folder.href

          return (
            <Link key={folder.href} href={folder.href}>
              <button
                className={cn(
                  'w-full flex items-center gap-3 px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-primary text-primary-foreground'
                    : 'text-foreground hover:bg-muted'
                )}
              >
                <Icon className="w-5 h-5 flex-shrink-0" />
                <span className="flex-1 text-left">{folder.label}</span>
                {folder.count > 0 && (
                  <span className={cn(
                    'px-2 py-0.5 rounded-full text-xs font-semibold',
                    isActive
                      ? 'bg-primary-foreground text-primary'
                      : 'bg-muted text-muted-foreground'
                  )}>
                    {folder.count}
                  </span>
                )}
              </button>
            </Link>
          )
        })}
      </div>

      <div className="pt-4 border-t border-border space-y-2">
        <p className="text-xs font-semibold text-muted-foreground px-4">LABELS</p>
        <div className="space-y-1">
          {['Work', 'Personal', 'Important'].map((label) => (
            <button
              key={label}
              className="w-full text-left px-4 py-2 rounded-lg text-sm text-muted-foreground hover:bg-muted transition-colors"
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      <MailComposer
        isOpen={isComposerOpen}
        onClose={() => setIsComposerOpen(false)}
        onSend={handleSendEmail}
      />
    </div>
  )
}
