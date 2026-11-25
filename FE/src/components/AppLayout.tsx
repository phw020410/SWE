import { useEffect, useRef, useState, type ReactNode } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { useConversations } from '../conversations/ConversationsContext'
import { conversationTitle } from '../lib/format'
import { IconChat, IconChevronDown, IconHelp, IconHistory, IconLock, IconLogout, IconMenu, IconPin, IconPlus, IconUser } from './Icons'
import { Logo } from './Logo'

function UserMenu() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    const onClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && setOpen(false)
    document.addEventListener('mousedown', onClick)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onClick)
      document.removeEventListener('keydown', onKey)
    }
  }, [open])

  if (!user) return null
  return (
    <div className="user-menu" ref={ref}>
      <button type="button" className="user-menu__trigger" onClick={() => setOpen((v) => !v)} aria-expanded={open} aria-haspopup="menu">
        <span className="avatar">{user.name.slice(0, 1)}</span>
        <span className="user-menu__name">{user.name} 님</span>
        <IconChevronDown size={16} />
      </button>
      {open && (
        <div className="user-menu__panel" role="menu">
          <div className="user-menu__info">
            <strong>{user.name}</strong>
            <span>{user.email}</span>
          </div>
          <button type="button" role="menuitem" onClick={() => { setOpen(false); navigate('/settings') }}>
            <IconUser size={16} /> 내 정보 수정
          </button>
          <button
            type="button"
            role="menuitem"
            onClick={async () => {
              setOpen(false)
              await logout()
              navigate('/login', { replace: true })
            }}
          >
            <IconLogout size={16} /> 로그아웃
          </button>
        </div>
      )}
    </div>
  )
}

function Sidebar({ guest, onNavigate }: { guest: boolean; onNavigate: () => void }) {
  const { conversations } = useConversations()
  const navigate = useNavigate()
  const recent = conversations.slice(0, 6)

  return (
    <aside className="sidebar">
      <button
        type="button"
        className="btn btn--primary btn--block btn--lg"
        onClick={() => {
          onNavigate()
          navigate(guest ? '/login' : '/chat', { state: { fresh: Date.now() } })
        }}
      >
        <IconPlus size={18} /> 새 대화 시작
      </button>

      <nav className="sidebar__nav" aria-label="주요 메뉴">
        <NavLink to={guest ? '/' : '/chat'} end={guest} className="sidebar__link" onClick={onNavigate}>
          <IconChat /> AI 맞춤 추천
        </NavLink>
        <NavLink to={guest ? '/login' : '/history'} className="sidebar__link" onClick={onNavigate}>
          <IconHistory /> 질의응답 내역 {guest && <IconLock size={14} className="sidebar__lock" />}
        </NavLink>
      </nav>

      <div className="sidebar__section">
        <p className="sidebar__label">최근 대화</p>
        {guest ? (
          <p className="sidebar__empty">로그인하면 나눈 대화를 이어서 볼 수 있어요.</p>
        ) : recent.length ? (
          <ul className="sidebar__recent">
            {recent.map((c) => (
              <li key={c.conversationId}>
                <NavLink to={`/chat/${c.conversationId}`} className="sidebar__recent-link" onClick={onNavigate} title={conversationTitle(c.title)}>
                  {conversationTitle(c.title)}
                </NavLink>
              </li>
            ))}
          </ul>
        ) : (
          <p className="sidebar__empty">아직 나눈 대화가 없어요.</p>
        )}
      </div>

      <div className="sidebar__promo">
        <IconPin size={18} />
        <strong>우리 동네에서, 한 걸음 더</strong>
        <p>부산의 교육부터 일자리까지, 나에게 맞는 길을 찾아보세요.</p>
      </div>

      <div className="sidebar__footer">
        <Link to="/guide" className="sidebar__help" onClick={onNavigate}>
          <IconHelp size={16} /> 도움이 필요하신가요?
        </Link>
        <p>© 2026 부산이음</p>
      </div>
    </aside>
  )
}

export function AppLayout({ children, guest = false }: { children: ReactNode; guest?: boolean }) {
  const [drawerOpen, setDrawerOpen] = useState(false)
  return (
    <div className={`app-shell${drawerOpen ? ' is-drawer-open' : ''}`}>
      <header className="topbar">
        <div className="topbar__left">
          <button type="button" className="icon-button topbar__menu" aria-label="메뉴 열기" onClick={() => setDrawerOpen((v) => !v)}>
            <IconMenu />
          </button>
          <Logo to={guest ? '/' : '/chat'} />
          <span className="topbar__divider" aria-hidden="true" />
          <span className="topbar__tagline">부산에서 찾는 나의 다음 기회</span>
        </div>
        <div className="topbar__right">
          <Link to="/guide" className="topbar__link">이용 안내</Link>
          {guest ? (
            <>
              <Link to="/signup" className="topbar__link topbar__link--strong">회원가입</Link>
              <Link to="/login" className="btn btn--primary btn--sm">로그인</Link>
            </>
          ) : (
            <UserMenu />
          )}
        </div>
      </header>
      <div className="app-body">
        <Sidebar guest={guest} onNavigate={() => setDrawerOpen(false)} />
        <div className="drawer-backdrop" onClick={() => setDrawerOpen(false)} aria-hidden="true" />
        <main className="main">{children}</main>
      </div>
    </div>
  )
}
