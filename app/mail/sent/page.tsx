'use client'

import { useState, useMemo } from 'react'
import useSWR from 'swr'
import MailListView from '@/components/mail/mail-list-view'
import MailDetailView from '@/components/mail/mail-detail-view'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const fetcher = (url: string) => {
  const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null
  return fetch(url, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  }).then(res => res.json())
}

interface MailServiceEmail {
  id: number
  sender: string
  recipient: string
  subject: string
  body: string
  status: string
  created_at: string
}

interface UIEmail {
  id: string
  from: string
  fromName: string
  to: string
  subject: string
  body: string
  preview: string
  read: boolean
  isDraft: boolean
  createdAt: string
  timestamp: Date
}

export default function SentPage() {
  const [selectedEmailId, setSelectedEmailId] = useState<string | null>(null)

  const { data: rawEmails, mutate } = useSWR(`${API_URL}/api/mails?box=sent`, fetcher)

  const emails: UIEmail[] = useMemo(() => {
    if (!Array.isArray(rawEmails)) return []
    return rawEmails.map((email: MailServiceEmail) => ({
      id: String(email.id),
      from: email.sender,
      fromName: email.sender.split('@')[0],
      to: email.recipient,
      subject: email.subject,
      body: email.body,
      preview: email.body.length > 80 ? email.body.substring(0, 80) + '...' : email.body,
      read: true,
      isDraft: false,
      createdAt: email.created_at,
      timestamp: new Date(email.created_at),
    }))
  }, [rawEmails])

  const selectedEmail = emails.find(email => email.id === selectedEmailId)

  const handleSelectEmail = (emailId: string) => {
    setSelectedEmailId(emailId)
  }

  const handleDeleteEmail = async (emailId: string) => {
    try {
      const token = localStorage.getItem('auth_token')
      await fetch(`${API_URL}/api/mails/${emailId}`, {
        method: 'DELETE',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })
      mutate(rawEmails?.filter((email: MailServiceEmail) => String(email.id) !== emailId))
      setSelectedEmailId(null)
    } catch (error) {
      console.error('Error deleting email:', error)
    }
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
