'use client'

import { useState, useMemo } from 'react'
import useSWR from 'swr'
import MailListView from '@/components/mail/mail-list-view'
import MailDetailView from '@/components/mail/mail-detail-view'
import MailSearch from '@/components/mail/mail-search'

const fetcher = (url: string) => {
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null
  return fetch(url, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  }).then(res => res.json())
}

interface DBEmail {
  id: string
  from: string
  fromName?: string
  to: string
  subject: string
  body: string
  preview?: string
  read: boolean
  isDraft: boolean
  createdAt: string
}

interface UIEmail extends DBEmail {
  timestamp: Date
}

export default function InboxPage() {
  const [selectedEmailId, setSelectedEmailId] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const { data: rawEmails = [], mutate } = useSWR('/api/emails', fetcher)

  // Transform database emails to UI format
  const emails: UIEmail[] = useMemo(() => {
    return rawEmails.map((email: DBEmail) => ({
      ...email,
      timestamp: new Date(email.createdAt),
      fromName: email.fromName || email.from.split('@')[0],
      preview: email.preview || email.body.substring(0, 50) + '...',
    }))
  }, [rawEmails])

  const selectedEmail = emails.find((email) => email.id === selectedEmailId)

  // Filter emails based on search query
  const filteredEmails = useMemo(() => {
    if (!searchQuery) return emails
    const query = searchQuery.toLowerCase()
    return emails.filter((email) =>
      email.subject.toLowerCase().includes(query) ||
      email.from.toLowerCase().includes(query) ||
      email.body.toLowerCase().includes(query)
    )
  }, [emails, searchQuery])

  const handleSelectEmail = (emailId: string) => {
    setSelectedEmailId(emailId)
  }

  const handleDeleteEmail = async (emailId: string) => {
    try {
      const token = localStorage.getItem('token')
      await fetch(`/api/emails/${emailId}`, {
        method: 'DELETE',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })
      mutate(rawEmails.filter((email: DBEmail) => email.id !== emailId))
      setSelectedEmailId(null)
    } catch (error) {
      console.error('Error deleting email:', error)
    }
  }

  return (
    <div className="flex h-full">
      <div className="flex-1 border-r border-border flex flex-col overflow-auto">
        <div className="p-4 border-b border-border flex-shrink-0">
          {/* <MailSearch onSearch={setSearchQuery} /> */}
        </div>
        <div className="flex-1 overflow-auto">
          <MailListView
            emails={filteredEmails}
            selectedEmailId={selectedEmailId}
            onSelectEmail={handleSelectEmail}
          />
        </div>
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
