'use client'

import { useState } from 'react'
import MailListView from '@/components/mail/mail-list-view'
import MailDetailView from '@/components/mail/mail-detail-view'

// Mock data
const mockEmails = [
  {
    id: '1',
    from: 'you@example.com',
    fromName: 'You (Draft)',
    subject: 'Important Announcement',
    preview: 'I wanted to inform you about...',
    body: 'I wanted to inform you about the upcoming changes to our project timeline.',
    timestamp: new Date(Date.now() - 30 * 60 * 1000),
    read: true,
  },
  {
    id: '2',
    from: 'you@example.com',
    fromName: 'You (Draft)',
    subject: 'Feedback Request',
    preview: 'Could you please review...',
    body: 'Could you please review the attached proposal and provide your feedback?',
    timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000),
    read: true,
  },
]

export default function DraftsPage() {
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
