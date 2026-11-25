import { useEffect, useMemo, useRef, useState, type KeyboardEvent } from 'react'
import { MAX_QUERY_LENGTH, validateImageFile } from '../lib/image'
import { IconClose, IconImage, IconLock, IconSend } from './Icons'

interface Props {
  value: string
  onChange: (value: string) => void
  image: File | null
  onImageChange: (file: File | null) => void
  onSubmit: () => void
  busy?: boolean
  locked?: boolean
  placeholder?: string
  onError?: (message: string) => void
}

export function Composer({ value, onChange, image, onImageChange, onSubmit, busy = false, locked = false, placeholder, onError }: Props) {
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const fileRef = useRef<HTMLInputElement>(null)
  const [dragging, setDragging] = useState(false)

  const previewUrl = useMemo(() => (image ? URL.createObjectURL(image) : null), [image])
  useEffect(() => () => {
    if (previewUrl) URL.revokeObjectURL(previewUrl)
  }, [previewUrl])

  // 입력 길이에 맞춰 높이 자동 조절
  useEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 180)}px`
  }, [value])

  const over = value.length > MAX_QUERY_LENGTH
  const canSend = !busy && !locked && !over && (!!image || value.trim().length > 0)

  function pick(file: File | undefined | null) {
    if (!file) return
    const problem = validateImageFile(file)
    if (problem) {
      onError?.(problem)
      return
    }
    onImageChange(file)
  }

  function onKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    // 한글 조합 중 Enter는 전송하지 않음
    if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault()
      if (canSend) onSubmit()
    }
  }

  if (locked) {
    return (
      <div className="composer composer--locked">
        <span className="composer__placeholder">{placeholder ?? '로그인하고 나에게 맞는 교육·취업 정보를 물어보세요'}</span>
        <span className="composer__lock" aria-hidden="true">
          <IconLock size={16} />
        </span>
      </div>
    )
  }

  return (
    <form
      className={`composer${dragging ? ' is-dragging' : ''}`}
      onSubmit={(e) => {
        e.preventDefault()
        if (canSend) onSubmit()
      }}
      onDragOver={(e) => {
        e.preventDefault()
        setDragging(true)
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault()
        setDragging(false)
        pick(e.dataTransfer.files?.[0])
      }}
    >
      {image && previewUrl && (
        <div className="composer__attachment">
          <img src={previewUrl} alt="첨부한 이미지 미리보기" />
          <div>
            <strong>{image.name}</strong>
            <span>{(image.size / 1024 / 1024).toFixed(1)}MB · 채용 공고나 교육 안내 이미지를 분석해요</span>
          </div>
          <button type="button" className="icon-button" onClick={() => onImageChange(null)} aria-label="첨부 이미지 삭제" disabled={busy}>
            <IconClose size={16} />
          </button>
        </div>
      )}
      <div className="composer__row">
        <button
          type="button"
          className="icon-button composer__attach"
          onClick={() => fileRef.current?.click()}
          disabled={busy}
          aria-label="이미지 첨부 (JPG, PNG, 5MB 이하)"
          title="이미지 첨부 (JPG, PNG, 5MB 이하)"
        >
          <IconImage size={20} />
        </button>
        <input
          ref={fileRef}
          type="file"
          accept=".jpg,.jpeg,.png,image/jpeg,image/png"
          hidden
          onChange={(e) => {
            pick(e.target.files?.[0])
            e.target.value = ''
          }}
        />
        <textarea
          ref={textareaRef}
          rows={1}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={onKeyDown}
          onPaste={(e) => {
            const file = Array.from(e.clipboardData.files).find((f) => f.type.startsWith('image/'))
            if (file) {
              e.preventDefault()
              pick(file)
            }
          }}
          placeholder={image ? '이미지를 보내면 내용을 분석해 드려요' : (placeholder ?? '궁금한 점이나 구체적인 조건을 알려주세요')}
          aria-label="질문 입력"
          disabled={busy || !!image}
          maxLength={MAX_QUERY_LENGTH + 200}
        />
        <button type="submit" className="composer__send" disabled={!canSend} aria-label="보내기">
          <IconSend size={18} />
        </button>
      </div>
      {(value.length > MAX_QUERY_LENGTH * 0.8 || over) && (
        <p className={`composer__count${over ? ' is-over' : ''}`}>
          {value.length.toLocaleString()} / {MAX_QUERY_LENGTH.toLocaleString()}자
        </p>
      )}
    </form>
  )
}
