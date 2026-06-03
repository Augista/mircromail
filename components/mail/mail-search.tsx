'use client'

import { useState, useCallback } from 'react'
import { Input } from '@/components/ui/input'
import { Search, X } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface MailSearchProps {
  onSearch: (query: string) => void
  placeholder?: string
}

export default function MailSearch({ onSearch, placeholder = 'Search emails...' }: MailSearchProps) {
  const [query, setQuery] = useState('')

  const handleSearch = useCallback((value: string) => {
    setQuery(value)
    onSearch(value)
  }, [onSearch])

  const handleClear = () => {
    setQuery('')
    onSearch('')
  }

  return (
    <div className="flex items-center gap-2 bg-muted rounded-lg px-3 py-2">
      <Search className="w-4 h-4 text-muted-foreground flex-shrink-0" />
      <Input
        type="text"
        placeholder={placeholder}
        value={query}
        onChange={(e) => handleSearch(e.target.value)}
        className="border-0 bg-transparent text-sm focus:ring-0 focus:outline-none"
      />
      {query && (
        <Button
          variant="ghost"
          size="sm"
          onClick={handleClear}
          className="h-6 w-6 p-0 flex-shrink-0"
        >
          <X className="w-4 h-4" />
        </Button>
      )}
    </div>
  )
}
