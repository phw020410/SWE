import { useId, useState, type InputHTMLAttributes } from 'react'
import { IconEye, IconEyeOff } from './Icons'

type Props = Omit<InputHTMLAttributes<HTMLInputElement>, 'type'> & { label: string; hint?: string; error?: string }

export function PasswordInput({ label, hint, error, id, ...rest }: Props) {
  const [visible, setVisible] = useState(false)
  const autoId = useId()
  const inputId = id ?? autoId
  return (
    <div className="field">
      <label htmlFor={inputId}>{label}</label>
      <div className={`input-wrap${error ? ' has-error' : ''}`}>
        <input id={inputId} type={visible ? 'text' : 'password'} aria-invalid={!!error} {...rest} />
        <button
          type="button"
          className="input-wrap__toggle"
          onClick={() => setVisible((v) => !v)}
          aria-label={visible ? '비밀번호 숨기기' : '비밀번호 보기'}
        >
          {visible ? <IconEye size={18} /> : <IconEyeOff size={18} />}
        </button>
      </div>
      {error ? <p className="field__error">{error}</p> : hint ? <p className="field__hint">{hint}</p> : null}
    </div>
  )
}

type TextProps = InputHTMLAttributes<HTMLInputElement> & { label: string; hint?: string; error?: string }

export function TextInput({ label, hint, error, id, ...rest }: TextProps) {
  const autoId = useId()
  const inputId = id ?? autoId
  return (
    <div className="field">
      <label htmlFor={inputId}>{label}</label>
      <div className={`input-wrap${error ? ' has-error' : ''}`}>
        <input id={inputId} aria-invalid={!!error} {...rest} />
      </div>
      {error ? <p className="field__error">{error}</p> : hint ? <p className="field__hint">{hint}</p> : null}
    </div>
  )
}
