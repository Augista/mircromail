'use client'

import { useState } from 'react'
import MailListView from '@/components/mail/mail-list-view'
import MailDetailView from '@/components/mail/mail-detail-view'

// Mock data
const mockEmails = [
  {
    id: '1',
    from: 'spam@example.com',
    fromName: 'Spam Email',
    subject: 'You won the lottery!',
    preview: 'Congratulations! You have won...',
    body: 'Congratulations! You have won $1,000,000. Click here to claim your prize.',
    timestamp: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000),
    read: true,
  },
]

export default function TrashPage() {
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
