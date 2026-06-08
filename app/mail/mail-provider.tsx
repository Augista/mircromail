'use client'

import { createContext, useContext, useState } from 'react'

type MailContextType = {
  searchQuery: string
  setSearchQuery: (v: string) => void
}

const MailContext = createContext<MailContextType | null>(null)

export function MailProvider({ children }: { children: React.ReactNode }) {
  const [searchQuery, setSearchQuery] = useState('')

  return (
    <MailContext.Provider value={{ searchQuery, setSearchQuery }}>
      {children}
    </MailContext.Provider>
  )
}

export function useMail() {
  const ctx = useContext(MailContext)
  if (!ctx) throw new Error('useMail must be used inside MailProvider')
  return ctx
}