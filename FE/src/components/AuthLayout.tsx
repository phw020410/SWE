import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { IconBriefcase, IconChat, IconGraduation, IconPin } from './Icons'
import { Logo } from './Logo'

/** 부산 바다와 다리를 표현한 일러스트 (외부 이미지 없이 SVG로 그림) */
function SeaIllustration() {
  return (
    <svg viewBox="0 0 400 260" className="auth-art__svg" role="img" aria-label="노을 지는 부산 바다와 다리 일러스트">
      <defs>
        <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#c9dbe0" />
          <stop offset=".55" stopColor="#f3dcc6" />
          <stop offset="1" stopColor="#f6c9a5" />
        </linearGradient>
        <linearGradient id="sea" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#6f97a1" />
          <stop offset="1" stopColor="#2f5f69" />
        </linearGradient>
        <linearGradient id="sand" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0" stopColor="#e9d8c2" />
          <stop offset="1" stopColor="#d9c3a6" />
        </linearGradient>
      </defs>
      <rect width="400" height="260" fill="url(#sky)" />
      <circle cx="300" cy="118" r="20" fill="#fbe4cc" opacity=".9" />
      {/* 도시 실루엣 */}
      <g fill="#7f97a0" opacity=".85">
        <rect x="10" y="88" width="14" height="44" />
        <rect x="27" y="72" width="11" height="60" />
        <rect x="41" y="96" width="16" height="36" />
        <rect x="60" y="80" width="10" height="52" />
        <rect x="335" y="92" width="12" height="40" />
        <rect x="350" y="78" width="16" height="54" />
        <rect x="369" y="100" width="20" height="32" />
      </g>
      {/* 다리 */}
      <g stroke="#55707a" strokeWidth="2" fill="none">
        <path d="M70 128 H340" strokeWidth="3" />
        <path d="M150 128 V92 M250 128 V92" strokeWidth="3" />
        <path d="M70 126 Q150 86 150 92 Q200 124 250 92 Q250 86 340 126" />
        {[90, 110, 130, 170, 190, 210, 230, 270, 290, 310].map((x) => (
          <path key={x} d={`M${x} 128 V${x < 150 ? 120 - (x - 70) * 0.35 : x < 250 ? 104 + Math.abs(200 - x) * 0.25 : 120 - (340 - x) * 0.3}`} strokeWidth="1" opacity=".7" />
        ))}
      </g>
      <rect y="132" width="400" height="70" fill="url(#sea)" />
      <path d="M0 150 Q40 146 80 150 T160 150 T240 150 T320 150 T400 150" stroke="#cfe2e5" strokeWidth="1.2" fill="none" opacity=".5" />
      <path d="M0 170 Q50 166 100 170 T200 170 T300 170 T400 170" stroke="#cfe2e5" strokeWidth="1.2" fill="none" opacity=".35" />
      <path d="M0 198 Q120 176 260 190 T400 184 V260 H0 Z" fill="url(#sand)" />
      <path d="M0 200 Q120 180 260 193 T400 188" stroke="#f5efe6" strokeWidth="3" fill="none" opacity=".8" />
    </svg>
  )
}

export function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="auth">
      <aside className="auth__panel">
        <Logo inverted />
        <div className="auth__copy">
          <p className="auth__eyebrow">
            <IconPin size={15} /> 부산의 가능성, 나의 가능성
          </p>
          <h1>
            내일의 나를,
            <br />
            부산에서 이어가다.
          </h1>
          <p>
            배우고 싶은 마음이 일할 수 있는 기회로.
            <br />
            부산이음이 당신의 다음 걸음을 함께 찾아드려요.
          </p>
        </div>
        <figure className="auth-art">
          <SeaIllustration />
          <figcaption>
            <IconPin size={13} /> 부산의 바다
          </figcaption>
        </figure>
        <ul className="auth__features">
          <li>
            <IconGraduation /> 나에게 맞는 교육
          </li>
          <li>
            <IconBriefcase /> 지역 일자리 탐색
          </li>
          <li>
            <IconChat /> 대화로 찾는 방향
          </li>
        </ul>
        <p className="auth__copyright">© 2026 부산이음 · 당신의 시작을 응원합니다.</p>
      </aside>
      <main className="auth__main">
        <div className="auth__form-wrap">{children}</div>
        <footer className="auth__footer">
          <Link to="/guide">이용 안내</Link>
          <Link to="/guide#privacy">개인정보 처리 안내</Link>
          <a href="https://github.com/phw020410/SWE" target="_blank" rel="noopener noreferrer">
            문의하기
          </a>
        </footer>
      </main>
    </div>
  )
}
