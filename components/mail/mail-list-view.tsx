'use client'

import { cn } from '@/lib/utils'
import { formatDistanceToNow } from 'date-fns'
import { Checkbox } from '@/components/ui/checkbox'

interface Email {
  id: string
  from: string
  fromName: string
  subject: string
  preview: string
  timestamp: Date
  read: boolean
}

interface MailListViewProps {
  emails: Email[]
  selectedEmailId: string | null
  onSelectEmail: (emailId: string) => void
}

export default function MailListView({
  emails,
  selectedEmailId,
  onSelectEmail,
}: MailListViewProps) {
  return (
    <div className="divide-y divide-border">
      {emails.length === 0 ? (
        <div className="flex items-center justify-center h-64 text-muted-foreground">
          No emails in this folder
        </div>
      ) : (
        emails.map((email) => (
          <button
            key={email.id}
            onClick={() => onSelectEmail(email.id)}
            className={cn(
              'w-full text-left px-4 py-3 hover:bg-muted transition-colors border border-bottom',
              selectedEmailId === email.id
                ? 'bg-muted border-l-primary'
                : email.read
                  ? 'bg-background'
                  : 'bg-background font-semibold'
            )}
          >
            <div className="flex items-start gap-3">
              {/* <Checkbox checked={false} className="mt-1 flex-shrink-0" aria-readonly /> */}
              <div className="flex-1 min-w-">
                <div className="flex items-center justify-between gap-2">
                  <p className="font-medium text-sm text-foreground truncate">
                    {email.fromName}
                  </p>
                  <span className="text-xs text-muted-foreground flex-shrink-0">
                    {formatDistanceToNow(email.timestamp, { addSuffix: false })}
                  </span>
                </div>
                <p className="text-sm text-foreground truncate mt-1">
                  {email.subject}
                </p>
                <p className="text-xs text-muted-foreground truncate mt-1">
                  {email.preview}
                </p>
              </div>
            </div>
          </button>
        ))
      )}
    </div>
  )
}
