'use client'

import { Button } from '@/components/ui/button'
import { formatDistanceToNow } from 'date-fns'
import { Reply, ReplyAll, Forward, Archive, Trash2 } from 'lucide-react'

interface Email {
  id: string
  from: string
  fromName: string
  subject: string
  preview: string
  body: string
  timestamp: Date
  read: boolean
}

interface MailDetailViewProps {
  email: Email
  onDelete: () => void
}

export default function MailDetailView({
  email,
  onDelete,
}: MailDetailViewProps) {
  return (
    <div className="flex flex-col h-full bg-card">
      {/* Header */}
      <div className="border-b border-border p-4">
        <h2 className="text-xl font-bold text-foreground">{email.subject}</h2>
      </div>

      {/* Email Info */}
      <div className="border-b border-border p-4">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-primary flex items-center justify-center text-primary-foreground font-semibold">
              {email.fromName.charAt(0).toUpperCase()}
            </div>
            <div>
              <p className="font-semibold text-foreground">{email.fromName}</p>
              <p className="text-xs text-muted-foreground">{email.from}</p>
            </div>
          </div>
          <span className="text-xs text-muted-foreground">
            {formatDistanceToNow(email.timestamp, { addSuffix: true })}
          </span>
        </div>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-auto p-4">
        <div className="prose dark:prose-invert max-w-none">
          <p className="text-sm text-foreground whitespace-pre-wrap">{email.body}</p>
        </div>
      </div>

      {/* Actions */}
      <div className="border-t border-border p-4 space-y-2">
        <div className="flex gap-2">
          <Button variant="outline" size="sm" className="flex-1">
            <Reply className="w-4 h-4 mr-2" />
            Reply
          </Button>
          <Button variant="outline" size="sm" className="flex-1">
            <ReplyAll className="w-4 h-4 mr-2" />
            Reply All
          </Button>
          <Button variant="outline" size="sm" className="flex-1">
            <Forward className="w-4 h-4 mr-2" />
            Forward
          </Button>
        </div>

        <div className="flex gap-2">
          <Button variant="outline" size="sm" className="flex-1">
            <Archive className="w-4 h-4 mr-2" />
            Archive
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="flex-1 text-destructive hover:text-destructive"
            onClick={onDelete}
          >
            <Trash2 className="w-4 h-4 mr-2" />
            Delete
          </Button>
        </div>
      </div>
    </div>
  )
}
