'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Search, Settings, LogOut, User } from 'lucide-react'
import { useMail } from '@/app/mail/mail-provider'

interface UserData {
  id: string
  email: string
  name: string
}

export default function MailHeader() {
  const router = useRouter()

  const [user, setUser] = useState<UserData | null>(null)
  const { setSearchQuery } = useMail()

  useEffect(() => {
    const storedUser = localStorage.getItem('user')
    if (storedUser) {
      try {
        setUser(JSON.parse(storedUser))
      } catch (error) {
        console.error('Error parsing user from storage:', error)
      }
    }
  }, [])

  const handleLogout = () => {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
    router.push('/login')
  }

  return (
    <div className="border-b border-border bg-card p-4 flex items-center justify-between gap-4">
      <div className="flex-1 flex items-center gap-2 bg-muted rounded-lg px-3 py-2">
        <Search className="w-4 h-4 text-muted-foreground shrink-0" />
        <Input
          type="search"
          placeholder="Search emails..."
          onChange={(e) => setSearchQuery(e.target.value)}
          className="border-0 bg-transparent text-sm focus:ring-0 focus:outline-none"
        />
      </div>

      <div className="flex items-center gap-2">
        <Button variant="ghost" size="icon" title="Settings">
          <Settings className="w-5 h-5" />
        </Button>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" title="User menu">
              <User className="w-5 h-5" />
            </Button>
          </DropdownMenuTrigger>

          <DropdownMenuContent align="end">
            <DropdownMenuItem disabled>
              Name : {user?.name || 'Loading...'}
            </DropdownMenuItem>

            <DropdownMenuItem disabled>
              Email : {user?.email}
            </DropdownMenuItem>

            <DropdownMenuItem onClick={handleLogout}>
              <LogOut className="w-4 h-4 mr-2" />
              Sign out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  )
}