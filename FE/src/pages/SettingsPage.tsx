import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { ApiError } from '../api/client'
import * as api from '../api/endpoints'
import { useAuth } from '../auth/AuthContext'
import { AppLayout } from '../components/AppLayout'
import { IconAlert, IconCheck } from '../components/Icons'
import { PasswordInput, TextInput } from '../components/PasswordInput'

/** FR-009: 이름·비밀번호 변경 (API-008) */
export function SettingsPage() {
  const { user, setUser, clearSession } = useAuth()
  const navigate = useNavigate()
  const [name, setName] = useState(user?.name ?? '')
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setSuccess(null)
    const trimmed = name.trim()
    const nameChanged = trimmed !== user?.name
    if (!trimmed) return setError('이름을 입력해 주세요.')
    if (!nameChanged && !newPassword) return setError('변경할 내용을 입력해 주세요.')
    if (currentPassword.length < 8) return setError('현재 비밀번호를 입력해 주세요.')
    if (newPassword && newPassword.length < 8) return setError('새 비밀번호는 8자 이상이어야 합니다.')
    if (newPassword !== confirm) return setError('새 비밀번호가 일치하지 않습니다.')

    setSaving(true)
    try {
      const updated = await api.updateMe({
        currentPassword,
        ...(nameChanged ? { name: trimmed } : {}),
        ...(newPassword ? { newPassword } : {}),
      })
      if (newPassword) {
        // 비밀번호를 바꾸면 서버가 기존 토큰을 무효화하므로 다시 로그인해야 한다
        clearSession(false)
        navigate('/login', { replace: true, state: { email: updated.email } })
        return
      }
      setUser(updated)
      setCurrentPassword('')
      setSuccess('정보가 변경되었어요.')
    } catch (err) {
      setError(err instanceof ApiError ? err.message : '정보를 변경하지 못했습니다.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <AppLayout>
      <div className="settings">
        <header className="page-head">
          <div>
            <h1 className="page-head__title">내 정보 수정</h1>
            <p className="page-head__sub">이름과 비밀번호를 바꿀 수 있어요. 비밀번호를 바꾸면 다시 로그인해야 해요.</p>
          </div>
        </header>
        <form className="card settings__form" onSubmit={onSubmit} noValidate>
          {error && (
            <div className="alert alert--error" role="alert">
              <IconAlert size={16} /> {error}
            </div>
          )}
          {success && (
            <div className="alert alert--success" role="status">
              <IconCheck size={16} /> {success}
            </div>
          )}
          <TextInput label="이메일" value={user?.email ?? ''} disabled readOnly />
          <TextInput label="이름" value={name} maxLength={50} onChange={(e) => setName(e.target.value)} autoComplete="name" />
          <hr />
          <PasswordInput label="새 비밀번호 (선택)" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} autoComplete="new-password" hint="바꾸지 않으려면 비워 두세요." />
          <PasswordInput label="새 비밀번호 확인" value={confirm} onChange={(e) => setConfirm(e.target.value)} autoComplete="new-password" />
          <hr />
          <PasswordInput
            label="현재 비밀번호"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            autoComplete="current-password"
            hint="본인 확인을 위해 꼭 입력해 주세요."
          />
          <button type="submit" className="btn btn--primary btn--lg" disabled={saving}>
            {saving ? '저장 중…' : '변경 내용 저장'}
          </button>
        </form>
      </div>
    </AppLayout>
  )
}
