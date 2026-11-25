import type { ReactNode } from 'react'
import { BrowserRouter, Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { AuthProvider, useAuth } from './auth/AuthContext'
import { ConversationsProvider } from './conversations/ConversationsContext'
import { ChatPage } from './pages/ChatPage'
import { GuidePage } from './pages/GuidePage'
import { HistoryPage } from './pages/HistoryPage'
import { LandingPage } from './pages/LandingPage'
import { LoginPage } from './pages/LoginPage'
import { SettingsPage } from './pages/SettingsPage'
import { SignupPage } from './pages/SignupPage'

/** 로그인이 필요한 화면. 미인증이면 로그인 화면으로 보내고, 로그인 후 원래 위치로 돌아온다. */
function RequireAuth({ children }: { children: ReactNode }) {
  const { isAuthenticated } = useAuth()
  const location = useLocation()
  if (!isAuthenticated) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  return children
}

/** 로그인·회원가입 화면. 이미 로그인 상태면 원래 가려던 곳(없으면 /chat)으로 보낸다. */
function GuestOnly({ children }: { children: ReactNode }) {
  const { isAuthenticated } = useAuth()
  const location = useLocation()
  const from = (location.state as { from?: string } | null)?.from
  return isAuthenticated ? <Navigate to={from ?? '/chat'} replace /> : children
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ConversationsProvider>
          <Routes>
            <Route path="/" element={<GuestOnly><LandingPage /></GuestOnly>} />
            <Route path="/login" element={<GuestOnly><LoginPage /></GuestOnly>} />
            <Route path="/signup" element={<GuestOnly><SignupPage /></GuestOnly>} />
            <Route path="/guide" element={<GuidePage />} />
            <Route path="/chat" element={<RequireAuth><ChatPage /></RequireAuth>} />
            <Route path="/chat/:conversationId" element={<RequireAuth><ChatPage /></RequireAuth>} />
            <Route path="/history" element={<RequireAuth><HistoryPage /></RequireAuth>} />
            <Route path="/history/:conversationId" element={<RequireAuth><HistoryPage /></RequireAuth>} />
            <Route path="/settings" element={<RequireAuth><SettingsPage /></RequireAuth>} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </ConversationsProvider>
      </AuthProvider>
    </BrowserRouter>
  )
}
