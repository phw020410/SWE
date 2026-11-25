import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ApiError } from '../api/client'
import * as api from '../api/endpoints'
import type { Conversation } from '../api/types'
import { useAuth } from '../auth/AuthContext'
import { AppLayout } from '../components/AppLayout'
import { AssistantAnswer } from '../components/AssistantAnswer'
import { IconAlert, IconChat, IconCheck, IconCopy, IconDownload, IconFile, IconImage, IconPlus, IconSearch, IconShield } from '../components/Icons'
import { Markdown } from '../components/Markdown'
import { useConversations } from '../conversations/ConversationsContext'
import { conversationTitle, formatDotDate, formatListStamp, formatTime } from '../lib/format'

function preview(conv: Conversation) {
  const first = conv.messages.find((m) => m.role === 'USER' && m.messageType === 'TEXT')
  const answer = conv.messages.filter((m) => m.role === 'ASSISTANT').length
  return { first: first?.content ?? (conv.messages.length ? '이미지 분석 대화' : ''), answer }
}

function downloadText(text: string, filename: string) {
  const blob = new Blob([text], { type: 'text/markdown;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}

function ExportPanel({ conversation }: { conversation: Conversation }) {
  const [mode, setMode] = useState<'preview' | 'raw'>('preview')
  const [markdown, setMarkdown] = useState<string | null>(null)
  const [filename, setFilename] = useState<string>('')
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  // API-004: 서버가 만든 Markdown을 불러와 미리보기·다운로드에 사용
  useEffect(() => {
    let cancelled = false
    setMarkdown(null)
    setError(null)
    api
      .exportConversation(conversation.conversationId)
      .then(({ text, filename: name }) => {
        if (cancelled) return
        setMarkdown(text)
        setFilename(name ?? `conversation-${conversation.conversationId}.md`)
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof ApiError ? err.message : 'Markdown을 불러오지 못했습니다.')
      })
    return () => {
      cancelled = true
    }
  }, [conversation.conversationId, conversation.updatedAt])

  async function copy() {
    if (!markdown) return
    try {
      await navigator.clipboard.writeText(markdown)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      setError('클립보드에 복사하지 못했습니다.')
    }
  }

  return (
    <section className="card export">
      <header className="export__head">
        <h3>
          <IconFile size={18} /> 교육·취업 정보 · Markdown
        </h3>
        <div className="export__actions">
          <div className="segmented" role="tablist" aria-label="보기 방식">
            <button type="button" role="tab" aria-selected={mode === 'preview'} className={mode === 'preview' ? 'is-active' : ''} onClick={() => setMode('preview')}>
              미리보기
            </button>
            <button type="button" role="tab" aria-selected={mode === 'raw'} className={mode === 'raw' ? 'is-active' : ''} onClick={() => setMode('raw')}>
              원본 Markdown
            </button>
          </div>
          <button type="button" className="btn btn--ghost btn--sm" onClick={copy} disabled={!markdown}>
            {copied ? <IconCheck size={15} /> : <IconCopy size={15} />} {copied ? '복사됨' : '텍스트 복사'}
          </button>
          <button type="button" className="btn btn--primary btn--sm" onClick={() => markdown && downloadText(markdown, filename)} disabled={!markdown}>
            <IconDownload size={15} /> .md 다운로드
          </button>
        </div>
      </header>
      {error ? (
        <div className="alert alert--error">
          <IconAlert size={16} /> {error}
        </div>
      ) : markdown === null ? (
        <p className="muted">불러오는 중…</p>
      ) : mode === 'preview' ? (
        <div className="export__body">
          <Markdown source={markdown} />
        </div>
      ) : (
        <pre className="export__raw">{markdown}</pre>
      )}
    </section>
  )
}

export function HistoryPage() {
  const { conversationId } = useParams()
  const navigate = useNavigate()
  const { user } = useAuth()
  const { conversations, loading, loaded, error, refresh } = useConversations()
  const [search, setSearch] = useState('')

  // UC-003: "조회" 시 서버에서 최신 이력을 다시 가져온다
  useEffect(() => {
    void refresh()
  }, [refresh])

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    if (!q) return conversations
    return conversations.filter(
      (c) => conversationTitle(c.title).toLowerCase().includes(q) || c.messages.some((m) => m.content.toLowerCase().includes(q)),
    )
  }, [conversations, search])

  const selected = conversations.find((c) => c.conversationId === conversationId) ?? (conversationId ? undefined : filtered[0])

  return (
    <AppLayout>
      <div className="history">
        <header className="page-head">
          <div>
            <h1 className="page-head__title">질의응답 내역</h1>
            <p className="page-head__sub">함께 찾은 방향을 다시 읽고, 다음 대화로 이어가세요.</p>
          </div>
          {loaded && <span className="pill">저장된 대화 {conversations.length}개</span>}
        </header>

        {error && (
          <div className="alert alert--error">
            <IconAlert size={16} /> {error}
            <button type="button" className="btn btn--ghost btn--sm" onClick={() => void refresh()}>
              다시 시도
            </button>
          </div>
        )}

        {loaded && conversations.length === 0 ? (
          // UC-003 2A: 이력이 없으면 새 대화 버튼 표시
          <div className="card empty-history">
            <IconChat size={28} />
            <h2>아직 나눈 대화가 없어요</h2>
            <p>관심 있는 직무나 분야를 물어보면, 대화가 여기에 차곡차곡 저장돼요.</p>
            <Link to="/chat" className="btn btn--primary">
              <IconPlus size={16} /> 새 대화 시작하기
            </Link>
          </div>
        ) : (
          <div className="history__grid">
            <div className="history__list">
              <label className="search">
                <IconSearch size={16} />
                <input type="search" placeholder="대화 제목 또는 내용 검색" value={search} onChange={(e) => setSearch(e.target.value)} aria-label="대화 검색" />
              </label>
              <p className="history__list-label">
                전체 대화 <span>최신순</span>
              </p>
              {!loaded && loading && <p className="muted">불러오는 중…</p>}
              <ul>
                {filtered.map((c) => {
                  const p = preview(c)
                  const active = selected?.conversationId === c.conversationId
                  return (
                    <li key={c.conversationId}>
                      <button
                        type="button"
                        className={`history-item${active ? ' is-active' : ''}`}
                        onClick={() => navigate(`/history/${c.conversationId}`)}
                        aria-current={active}
                      >
                        <span className="history-item__stamp">{formatListStamp(c.updatedAt)}</span>
                        <strong>{conversationTitle(c.title)}</strong>
                        <span className="history-item__preview">{p.first}</span>
                        {active && <IconCheck size={16} className="history-item__check" />}
                      </button>
                    </li>
                  )
                })}
                {loaded && filtered.length === 0 && <li className="muted">검색 결과가 없어요.</li>}
              </ul>
              <p className="history__privacy">
                <IconShield size={14} /> 내 대화는 나만 볼 수 있어요.
              </p>
            </div>

            <div className="history__detail">
              {selected ? (
                <>
                  <div className="history__detail-head">
                    <div>
                      <h2>{conversationTitle(selected.title)}</h2>
                      <p className="muted">
                        {formatDotDate(selected.createdAt)} · {formatTime(selected.createdAt)}~{formatTime(selected.updatedAt)} · 메시지 {selected.messages.length}개
                      </p>
                    </div>
                    <Link to={`/chat/${selected.conversationId}`} className="btn btn--outline btn--sm">
                      <IconChat size={16} /> 이어서 대화하기
                    </Link>
                  </div>

                  <section className="card transcript">
                    <h3 className="card__title">대화 내용</h3>
                    {selected.messages.map((m) => (
                      <div key={m.messageId} className={`transcript__item is-${m.role.toLowerCase()}`}>
                        <p className="transcript__who">
                          <strong>{m.role === 'USER' ? `나 · ${user?.name ?? ''}` : '부산이음 AI'}</strong>
                          <span>{formatTime(m.createdAt)}</span>
                        </p>
                        {m.role === 'USER' ? (
                          m.messageType === 'IMAGE' ? (
                            <p className="transcript__image">
                              <IconImage size={15} /> 이미지 분석 요청
                              {m.imageAnalysis && typeof m.imageAnalysis.title === 'string' ? ` · ${m.imageAnalysis.title}` : ''}
                            </p>
                          ) : (
                            <p>{m.content}</p>
                          )
                        ) : (
                          <AssistantAnswer content={m.content} items={m.items ?? []} />
                        )}
                      </div>
                    ))}
                  </section>

                  <ExportPanel conversation={selected} />
                </>
              ) : loaded && conversationId ? (
                <div className="card empty-history">
                  <h2>대화를 찾을 수 없어요</h2>
                  <Link to="/history" className="btn btn--outline btn--sm">
                    목록으로
                  </Link>
                </div>
              ) : null}
            </div>
          </div>
        )}
      </div>
    </AppLayout>
  )
}
