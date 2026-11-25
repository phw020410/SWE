import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { ApiError } from '../api/client'
import * as api from '../api/endpoints'
import type { Conversation } from '../api/types'
import { useAuth } from '../auth/AuthContext'

interface ConversationsValue {
  conversations: Conversation[]
  loading: boolean
  loaded: boolean
  error: string | null
  refresh: () => Promise<Conversation[]>
}

const ConversationsContext = createContext<ConversationsValue | null>(null)

/** 대화 이력(API-003)을 한 곳에서 불러와 사이드바·채팅·내역 화면이 함께 쓴다. */
export function ConversationsProvider({ children }: { children: ReactNode }) {
  const { isAuthenticated } = useAuth()
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [loading, setLoading] = useState(false)
  const [loaded, setLoaded] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const list = await api.getHistory(100, 0)
      const sorted = [...list].sort((a, b) => b.updatedAt.localeCompare(a.updatedAt))
      setConversations(sorted)
      setLoaded(true)
      return sorted
    } catch (err) {
      setError(err instanceof ApiError ? err.message : '대화 내역을 불러오지 못했습니다.')
      return []
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (isAuthenticated) {
      void refresh()
    } else {
      setConversations([])
      setLoaded(false)
    }
  }, [isAuthenticated, refresh])

  const value = useMemo(
    () => ({ conversations, loading, loaded, error, refresh }),
    [conversations, loading, loaded, error, refresh],
  )
  return <ConversationsContext.Provider value={value}>{children}</ConversationsContext.Provider>
}
export function useConversations() {
  const ctx = useContext(ConversationsContext)
  if (!ctx) throw new Error('useConversations must be used within ConversationsProvider')
  return ctx
}
