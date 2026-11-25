import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { setAccessToken, setUnauthorizedHandler } from '../api/client'
import * as api from '../api/endpoints'
import type { User } from '../api/types'
import { readJson, remove, writeJson } from '../lib/storage'

const STORAGE_KEY = 'busan-ieum.session'

interface Session {
  token: string
  expiresAt: number // epoch ms
  user: User
}

interface AuthValue {
  user: User | null
  isAuthenticated: boolean
  /** 토큰 만료·무효로 로그아웃된 직후 true (로그인 화면 안내용) */
  sessionExpired: boolean
  login: (email: string, password: string) => Promise<void>
  signup: (email: string, password: string, name: string) => Promise<void>
  logout: () => Promise<void>
  /** 서버 호출 없이 로컬 세션만 정리 (비밀번호 변경 후 등) */
  clearSession: (expired?: boolean) => void
  setUser: (user: User) => void
}

const AuthContext = createContext<AuthValue | null>(null)

function loadSession(): Session | null {
  const saved = readJson<Session>(STORAGE_KEY)
  if (!saved?.token || !saved.expiresAt || saved.expiresAt <= Date.now()) {
    remove(STORAGE_KEY)
    return null
  }
  return saved
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(() => {
    const saved = loadSession()
    setAccessToken(saved?.token ?? null)
    return saved
  })
  const [sessionExpired, setSessionExpired] = useState(false)

  const apply = useCallback((next: Session | null) => {
    setAccessToken(next?.token ?? null)
    if (next) writeJson(STORAGE_KEY, next)
    else remove(STORAGE_KEY)
    setSession(next)
  }, [])

  const clearSession = useCallback(
    (expired = false) => {
      apply(null)
      setSessionExpired(expired)
    },
    [apply],
  )

  // 보호 API에서 401 → 세션 정리 후 로그인 화면으로 (ProtectedRoute가 이동 처리)
  useEffect(() => {
    setUnauthorizedHandler(() => clearSession(true))
    return () => setUnauthorizedHandler(null)
  }, [clearSession])

  // 토큰 만료 시각에 맞춰 자동 로그아웃
  useEffect(() => {
    if (!session) return
    const timer = window.setTimeout(() => clearSession(true), Math.max(0, session.expiresAt - Date.now()))
    return () => window.clearTimeout(timer)
  }, [session, clearSession])

  // 새로고침 후 저장된 토큰이 아직 유효한지 확인하고 사용자 정보를 갱신
  useEffect(() => {
    if (!session) return
    let cancelled = false
    api
      .getMe()
      .then((user) => {
        if (!cancelled) setSession((prev) => (prev ? { ...prev, user } : prev))
      })
      .catch(() => {
        // 401은 unauthorizedHandler가 처리. 네트워크 오류는 저장된 정보로 계속 사용.
      })
    return () => {
      cancelled = true
    }
    // 최초 1회만 실행 (session 변경마다 다시 부르지 않음)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const login = useCallback(
    async (email: string, password: string) => {
      const res = await api.login({ email, password })
      setSessionExpired(false)
      apply({ token: res.accessToken, expiresAt: Date.now() + res.expiresIn * 1000 - 5000, user: res.user })
    },
    [apply],
  )

  const signup = useCallback(
    async (email: string, password: string, name: string) => {
      await api.signup({ email, password, name })
      await login(email, password)
    },
    [login],
  )

  const logout = useCallback(async () => {
    try {
      await api.logout()
    } catch {
      // 서버 로그아웃 실패해도 로컬 토큰은 삭제
    }
    clearSession(false)
  }, [clearSession])

  const setUser = useCallback(
    (user: User) => {
      setSession((prev) => {
        if (!prev) return prev
        const next = { ...prev, user }
        writeJson(STORAGE_KEY, next)
        return next
      })
    },
    [],
  )

  const value = useMemo<AuthValue>(
    () => ({
      user: session?.user ?? null,
      isAuthenticated: !!session,
      sessionExpired,
      login,
      signup,
      logout,
      clearSession,
      setUser,
    }),
    [session, sessionExpired, login, signup, logout, clearSession, setUser],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
