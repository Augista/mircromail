import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'MicroMail - Sign In',
  description: 'Sign in to your MicroMail account',
}

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4 py-12 sm:px-6 lg:px-8">
      <div className="w-full max-w-md">
        {children}
      </div>
    </div>
  )
}
