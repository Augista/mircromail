import type { Metadata } from 'next'
import MailSidebar from '@/components/mail/mail-sidebar'
import MailHeader from '@/components/mail/mail-header'
import { MailProvider } from './mail-provider'

export const metadata: Metadata = {
  title: 'MicroMail - Inbox',
  description: 'Your email inbox',
}

export default function MailLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <MailProvider>
    <div className="flex h-screen bg-background">
      <MailSidebar />
      <div className="flex-1 flex flex-col">
        <MailHeader />
        <main className="flex-1 overflow-auto">
          {children}
        </main>
      </div>
    </div>
    </MailProvider>
  )
}
