import { useState, type FormEvent } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { ApiError } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { AuthLayout } from '../components/AuthLayout'
import { IconAlert, IconArrowLeft } from '../components/Icons'
import { PasswordInput, TextInput } from '../components/PasswordInput'

export function LoginPage() {
  const { login, sessionExpired } = useAuth()
  const location = useLocation()
  const signedUpEmail = (location.state as { email?: string } | null)?.email ?? ''

  const [email, setEmail] = useState(signedUpEmail)
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    if (!email.trim() || !password) {
      setError('이메일과 비밀번호를 입력해 주세요.')
      return
    }
    setSubmitting(true)
    setError(null)
    try {
      // 이동은 GuestOnly(App.tsx)가 state.from 을 보고 처리한다
      await login(email.trim(), password)
    } catch (err) {
      // FR-008: 잘못된 정보 입력 시 오류 메시지 출력 (계정 존재 여부는 노출하지 않음)
      setError(err instanceof ApiError ? err.message : '로그인에 실패했습니다. 다시 시도해 주세요.')
      setPassword('')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthLayout>
      <Link to="/" className="back-link">
        <IconArrowLeft size={16} /> 처음 화면으로
      </Link>
      <div className="auth-form">
        <p className="auth-form__eyebrow">부산에서 찾는 나의 다음 기회</p>
        <h2>다시 만나 반가워요</h2>
        <p className="auth-form__lead">로그인하고 이어서 교육·취업 추천을 받아보세요.</p>

        {sessionExpired && !error && (
          <div className="alert alert--info" role="status">
            <IconAlert size={16} /> 로그인이 만료되었어요. 다시 로그인해 주세요.
          </div>
        )}
        {error && (
          <div className="alert alert--error" role="alert">
            <IconAlert size={16} /> {error}
          </div>
        )}

        <form onSubmit={onSubmit} noValidate>
          <TextInput
            label="이메일"
            type="email"
            autoComplete="email"
            placeholder="예: hello@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <PasswordInput
            label="비밀번호"
            autoComplete="current-password"
            placeholder="비밀번호를 입력해 주세요"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <button type="submit" className="btn btn--primary btn--block btn--lg" disabled={submitting}>
            {submitting ? '로그인 중…' : '로그인'}
          </button>
        </form>
        <p className="auth-form__switch">
          아직 계정이 없으신가요? <Link to="/signup">회원가입</Link>
        </p>
      </div>
    </AuthLayout>
  )
}
