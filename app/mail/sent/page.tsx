'use client'

import { useState } from 'react'
import MailListView from '@/components/mail/mail-list-view'
import MailDetailView from '@/components/mail/mail-detail-view'

// Mock data
const mockEmails = [
  {
    id: '1',
    from: 'you@example.com',
    fromName: 'You',
    subject: 'Re: Project Update',
    preview: 'Thanks for the update...',
    body: 'Thanks for the update. I will review the documents and get back to you.',
    timestamp: new Date(Date.now() - 1 * 60 * 60 * 1000),
    read: true,
  },
  {
    id: '2',
    from: 'you@example.com',
    fromName: 'You',
    subject: 'Meeting Notes',
    preview: 'Here are the notes from today...',
    body: 'Here are the notes from todays meeting. Please review and provide feedback.',
    timestamp: new Date(Date.now() - 3 * 60 * 60 * 1000),
    read: true,
  },
]

export default function SentPage() {
  const [selectedEmailId, setSelectedEmailId] = useState<string | null>(null)
  const [emails, setEmails] = useState(mockEmails)

  const selectedEmail = emails.find(email => email.id === selectedEmailId)

  const handleSelectEmail = (emailId: string) => {
    setSelectedEmailId(emailId)
  }

  const handleDeleteEmail = (emailId: string) => {
    setEmails(emails.filter(email => email.id !== emailId))
    setSelectedEmailId(null)
  }

  return (
    <div className="flex h-full">
      <div className="flex-1 border-r border-border overflow-auto">
        <MailListView
          emails={emails}
          selectedEmailId={selectedEmailId}
          onSelectEmail={handleSelectEmail}
        />
      </div>
      {selectedEmail && (
        <div className="w-1/2 overflow-auto">
          <MailDetailView
            email={selectedEmail}
            onDelete={() => handleDeleteEmail(selectedEmail.id)}
          />
        </div>
      )}
    </div>
  )
}
