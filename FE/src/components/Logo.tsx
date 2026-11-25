import { Link } from 'react-router-dom'

export function LogoMark({ size = 32, inverted = false }: { size?: number; inverted?: boolean }) {
  const bg = inverted ? 'rgba(255,255,255,0.14)' : '#0E7C76'
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" fill="none" aria-hidden="true">
      <rect width="48" height="48" rx="12" fill={bg} />
      <path d="M10 18c3.5-3 7-3 10.5 0s7 3 10.5 0 5.5-2.2 7-1.6" stroke="#fff" strokeWidth="3" strokeLinecap="round" />
      <path d="M10 25c3.5-3 7-3 10.5 0s7 3 10.5 0 5.5-2.2 7-1.6" stroke="#fff" strokeWidth="3" strokeLinecap="round" opacity=".85" />
      <path d="M10 32c3.5-3 7-3 10.5 0s7 3 10.5 0 5.5-2.2 7-1.6" stroke="#fff" strokeWidth="3" strokeLinecap="round" opacity=".65" />
    </svg>
  )
}

export function Logo({ inverted = false, to = '/' }: { inverted?: boolean; to?: string }) {
  return (
    <Link to={to} className={`logo${inverted ? ' logo--inverted' : ''}`} aria-label="부산이음 홈">
      <LogoMark inverted={inverted} />
      <span>부산이음</span>
    </Link>
  )
}
