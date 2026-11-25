import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ApiError } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { AuthLayout } from '../components/AuthLayout'
import { IconAlert, IconArrowLeft, IconCheck } from '../components/Icons'
import { PasswordInput, TextInput } from '../components/PasswordInput'

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

type Errors = Partial<Record<'email' | 'name' | 'password' | 'confirm' | 'terms', string>>

const TERMS = [
  { key: 'service', label: '[필수] 서비스 이용약관 동의', required: true },
  { key: 'privacy', label: '[필수] 개인정보 수집 및 이용 동의 (이메일·이름)', required: true },
  { key: 'news', label: '[선택] 교육·취업 소식 수신 동의', required: false },
] as const

type TermKey = (typeof TERMS)[number]['key']

function utf8Length(value: string) {
  return new TextEncoder().encode(value).length
}

export function SignupPage() {
  const { signup } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [name, setName] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [agreed, setAgreed] = useState<Record<TermKey, boolean>>({ service: false, privacy: false, news: false })
  const [errors, setErrors] = useState<Errors>({})
  const [serverError, setServerError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const allAgreed = TERMS.every((t) => agreed[t.key])

  function validate(): Errors {
    const next: Errors = {}
    if (!EMAIL_RE.test(email.trim())) next.email = '올바른 이메일 주소를 입력해 주세요.'
    if (!name.trim()) next.name = '이름을 입력해 주세요.'
    else if (name.trim().length > 50) next.name = '이름은 50자 이하로 입력해 주세요.'
    if (password.length < 8) next.password = '비밀번호는 8자 이상이어야 합니다.'
    else if (utf8Length(password) > 72) next.password = '비밀번호가 너무 깁니다.'
    if (confirm !== password) next.confirm = '비밀번호가 일치하지 않습니다.'
    if (!agreed.service || !agreed.privacy) next.terms = '필수 약관에 동의해 주세요.'
    return next
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    const next = validate()
    setErrors(next)
    setServerError(null)
    if (Object.keys(next).length) return
    setSubmitting(true)
    try {
      await signup(email.trim(), password, name.trim())
      navigate('/chat', { replace: true })
    } catch (err) {
      if (err instanceof ApiError && err.code === 'DUPLICATE_EMAIL') {
        setErrors({ email: err.message })
      } else {
        setServerError(err instanceof ApiError ? err.message : '회원가입에 실패했습니다. 다시 시도해 주세요.')
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthLayout>
      <Link to="/login" className="back-link">
        <IconArrowLeft size={16} /> 로그인으로 돌아가기
      </Link>
      <div className="auth-form">
        <p className="auth-form__eyebrow">당신의 다음 기회를 함께 찾아요</p>
        <h2>부산이음 시작하기</h2>
        <p className="auth-form__lead">이메일로 간편하게 가입하고, 나만의 교육·취업 추천을 대화로 만나보세요.</p>

        {serverError && (
          <div className="alert alert--error" role="alert">
            <IconAlert size={16} /> {serverError}
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
            error={errors.email}
          />
          <TextInput
            label="이름"
            autoComplete="name"
            placeholder="이름을 입력해 주세요"
            maxLength={50}
            value={name}
            onChange={(e) => setName(e.target.value)}
            error={errors.name}
          />
          <PasswordInput
            label="비밀번호"
            autoComplete="new-password"
            placeholder="비밀번호를 설정해 주세요"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            hint="8자 이상 입력해 주세요. 영문, 숫자, 특수문자를 섞으면 더 안전해요."
            error={errors.password}
          />
          <PasswordInput
            label="비밀번호 확인"
            autoComplete="new-password"
            placeholder="비밀번호를 한 번 더 입력해 주세요"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            error={errors.confirm}
          />

          <fieldset className="terms">
            <legend className="sr-only">약관 동의</legend>
            <label className="terms__all">
              <input
                type="checkbox"
                checked={allAgreed}
                onChange={(e) => setAgreed({ service: e.target.checked, privacy: e.target.checked, news: e.target.checked })}
              />
              <span className="checkbox" aria-hidden="true"><IconCheck size={13} /></span>
              모든 약관에 동의합니다
            </label>
            {TERMS.map((t) => (
              <label key={t.key} className="terms__item">
                <input type="checkbox" checked={agreed[t.key]} onChange={(e) => setAgreed((prev) => ({ ...prev, [t.key]: e.target.checked }))} />
                <span className="checkbox" aria-hidden="true"><IconCheck size={13} /></span>
                {t.label}
              </label>
            ))}
            {errors.terms && <p className="field__error">{errors.terms}</p>}
          </fieldset>

          <button type="submit" className="btn btn--primary btn--block btn--lg" disabled={submitting}>
            {submitting ? '가입 중…' : '동의하고 회원가입'}
          </button>
        </form>
        <p className="auth-form__switch">
          이미 계정이 있으신가요? <Link to="/login">로그인</Link>
        </p>
      </div>
    </AuthLayout>
  )
}
