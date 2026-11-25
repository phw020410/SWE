import { useCallback, useEffect, useRef, useState } from 'react'
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'
import { ApiError } from '../api/client'
import * as api from '../api/endpoints'
import type { Conversation, HistoryMessage, RecommendedItem } from '../api/types'
import { useAuth } from '../auth/AuthContext'
import { AppLayout } from '../components/AppLayout'
import { AssistantAnswer } from '../components/AssistantAnswer'
import { Composer } from '../components/Composer'
import { MAX_QUERY_LENGTH } from '../lib/image'
import { IconAlert, IconClose, IconHistory, IconImage, IconSparkle } from '../components/Icons'
import { LogoMark } from '../components/Logo'
import { useConversations } from '../conversations/ConversationsContext'
import { conversationTitle, formatDate, formatTime, isSameDay } from '../lib/format'

interface ChatMessage {
  key: string
  role: 'USER' | 'ASSISTANT'
  type: 'TEXT' | 'IMAGE'
  content: string
  createdAt: string
  items: RecommendedItem[]
  notices?: string[]
  imageUrl?: string
  imageName?: string
  imageTitle?: string
}

const EXAMPLES = [
  '부산에서 데이터 분석 일을 시작하고 싶어요. 비전공자도 들을 수 있는 교육이 있을까요?',
  '부산 백엔드 개발 신입 채용이랑 관련 교육 알려줘',
  '디자인 쪽 교육만 3개 추천해 줘',
  '최근에 올라온 부산 교육·채용 정보 보여줘',
]

const FOLLOW_UPS = ['교육만 3개 더 보여줘', '신입 채용만 알려줘', '최근 등록된 정보로 보여줘']

function fromHistory(message: HistoryMessage): ChatMessage {
  const title = message.imageAnalysis && typeof message.imageAnalysis.title === 'string' ? message.imageAnalysis.title : undefined
  return {
    key: message.messageId,
    role: message.role,
    type: message.messageType,
    content: message.content,
    createdAt: message.createdAt,
    items: message.items ?? [],
    imageTitle: title,
  }
}

function TypingBubble({ image }: { image: boolean }) {
  return (
    <div className="msg msg--assistant">
      <div className="msg__author">
        <LogoMark size={26} />
        <strong>부산이음 AI</strong>
      </div>
      <div className="typing" role="status">
        <span className="typing__dots" aria-hidden="true">
          <i />
          <i />
          <i />
        </span>
        {image ? '이미지에서 채용·교육 정보를 읽고 있어요…' : '부산의 교육·채용 정보를 찾고 있어요…'}
      </div>
    </div>
  )
}

function UserBubble({ message }: { message: ChatMessage }) {
  return (
    <div className="msg msg--user">
      {message.type === 'IMAGE' ? (
        <div className="bubble bubble--image">
          {message.imageUrl ? (
            <img src={message.imageUrl} alt={message.imageName ?? '업로드한 이미지'} />
          ) : (
            <span className="bubble__file">
              <IconImage size={16} /> {message.imageTitle ? `이미지 분석: ${message.imageTitle}` : '이미지 분석 요청'}
            </span>
          )}
        </div>
      ) : (
        <div className="bubble">{message.content}</div>
      )}
      <span className="msg__time">{formatTime(message.createdAt)}</span>
    </div>
  )
}

function AssistantBubble({ message }: { message: ChatMessage }) {
  return (
    <div className="msg msg--assistant">
      <div className="msg__author">
        <LogoMark size={26} />
        <strong>부산이음 AI</strong>
        <span className="badge badge--teal">{message.type === 'IMAGE' ? '이미지 분석' : '커리어 길잡이'}</span>
      </div>
      <div className="msg__body">
        <AssistantAnswer content={message.content} items={message.items} />
        {message.notices && message.notices.length > 0 && (
          <ul className="msg__notices">
            {message.notices.map((n) => (
              <li key={n}>
                <IconAlert size={14} /> {n}
              </li>
            ))}
          </ul>
        )}
      </div>
      <span className="msg__time">{formatTime(message.createdAt)}</span>
    </div>
  )
}

function EmptyState({ name, onPick }: { name?: string; onPick: (q: string) => void }) {
  return (
    <div className="empty-chat">
      <p className="eyebrow">
        <IconSparkle size={15} /> 부산의 교육과 취업, 대화로 가볍게
      </p>
      <h1>{name ? `${name} 님, 어디서 시작해 볼까요?` : '어디서 시작할지 막막할 때, 부산이음'}</h1>
      <p className="lead">관심 직무와 희망 지역을 알려주세요. 나에게 맞는 배움과 일의 방향을 함께 찾아드려요.</p>
      <div className="empty-chat__grid">
        <div className="card">
          <h2 className="card__title">이렇게 물어보세요</h2>
          <div className="examples">
            {EXAMPLES.map((q) => (
              <button key={q} type="button" className="example" onClick={() => onPick(q)}>
                {q}
              </button>
            ))}
          </div>
        </div>
        <div className="card steps">
          <h2 className="card__title">가볍게 말하면, 함께 찾아요</h2>
          <ol>
            <li>
              <strong>나의 관심사 이야기하기</strong>
              <span>직무, 경험, 희망 지역을 편하게 말해요.</span>
            </li>
            <li>
              <strong>맞춤 추천 살펴보기</strong>
              <span>고용24·청년 일자리 정보를 근거로 추천해요.</span>
            </li>
            <li>
              <strong>이미지로도 물어보기</strong>
              <span>채용 공고·교육 안내 이미지를 올리면 핵심만 정리해요.</span>
            </li>
          </ol>
        </div>
      </div>
    </div>
  )
}

export function ChatPage() {
  const { conversationId } = useParams()
  const location = useLocation()
  const navigate = useNavigate()
  const { user } = useAuth()
  const { conversations, refresh } = useConversations()

  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [activeId, setActiveId] = useState<string | null>(conversationId ?? null)
  const [title, setTitle] = useState<string | null>(null)
  const [text, setText] = useState('')
  const [image, setImage] = useState<File | null>(null)
  const [busy, setBusy] = useState<false | 'text' | 'image'>(false)
  const [error, setError] = useState<string | null>(null)
  const [loadState, setLoadState] = useState<'idle' | 'loading' | 'missing'>('idle')
  const [showNotice, setShowNotice] = useState(true)

  const conversationsRef = useRef<Conversation[]>(conversations)
  const justCreated = useRef<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)
  const objectUrls = useRef<string[]>([])

  useEffect(() => {
    conversationsRef.current = conversations
  }, [conversations])

  // 화면을 떠날 때 진행 중 요청 취소, 미리보기 URL 해제
  useEffect(
    () => () => {
      abortRef.current?.abort()
      objectUrls.current.forEach((u) => URL.revokeObjectURL(u))
    },
    [],
  )

  // URL의 대화 ID가 바뀌면 해당 대화를 불러온다
  useEffect(() => {
    if (conversationId && justCreated.current === conversationId) {
      justCreated.current = null
      return
    }
    abortRef.current?.abort()
    setBusy(false)
    setError(null)
    setImage(null)
    setActiveId(conversationId ?? null)

    if (!conversationId) {
      setMessages([])
      setTitle(null)
      setLoadState('idle')
      return
    }

    let cancelled = false
    const apply = (conv: Conversation) => {
      setMessages(conv.messages.map(fromHistory))
      setTitle(conv.title)
      setLoadState('idle')
    }
    const cached = conversationsRef.current.find((c) => c.conversationId === conversationId)
    if (cached) {
      apply(cached)
    } else {
      setMessages([])
      setLoadState('loading')
      refresh().then((list) => {
        if (cancelled) return
        const found = list.find((c) => c.conversationId === conversationId)
        if (found) apply(found)
        else setLoadState('missing')
      })
    }
    return () => {
      cancelled = true
    }
    // location.key: 같은 /chat 에서 "새 대화 시작"을 눌러도 초기화되도록
  }, [conversationId, location.key, refresh])

  // 새 메시지가 생기면 맨 아래로 스크롤 (페이지 전체가 스크롤 영역)
  useEffect(() => {
    if (!messages.length) return
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    window.scrollTo({ top: document.documentElement.scrollHeight, behavior: reduce ? 'auto' : 'smooth' })
  }, [messages, busy])

  const afterResponse = useCallback(
    (newConversationId: string, firstQuery: string) => {
      if (!activeId) {
        setActiveId(newConversationId)
        setTitle(firstQuery.slice(0, 30))
        justCreated.current = newConversationId
        navigate(`/chat/${newConversationId}`, { replace: true })
      }
      void refresh()
    },
    [activeId, navigate, refresh],
  )

  async function sendText(raw: string) {
    const query = raw.trim()
    if (!query || busy) return
    if (query.length > MAX_QUERY_LENGTH) {
      setError(`질문은 ${MAX_QUERY_LENGTH.toLocaleString()}자 이하로 입력해 주세요.`)
      return
    }
    const controller = new AbortController()
    abortRef.current = controller
    const tempKey = `pending-${Date.now()}`
    setMessages((prev) => [...prev, { key: tempKey, role: 'USER', type: 'TEXT', content: query, createdAt: new Date().toISOString(), items: [] }])
    setText('')
    setError(null)
    setBusy('text')
    try {
      const res = await api.sendQuery({ query, conversationId: activeId }, controller.signal)
      setMessages((prev) => [
        ...prev,
        { key: res.messageId, role: 'ASSISTANT', type: 'TEXT', content: res.answer, createdAt: new Date().toISOString(), items: res.items ?? [], notices: res.notices },
      ])
      afterResponse(res.conversationId, query)
    } catch (err) {
      if (controller.signal.aborted) return
      // 실패 시 보낸 질문을 입력창에 되돌려 다시 시도할 수 있게 한다
      setMessages((prev) => prev.filter((m) => m.key !== tempKey))
      setText(query)
      setError(err instanceof ApiError ? err.message : '요청을 처리하지 못했습니다. 다시 시도해 주세요.')
    } finally {
      if (!controller.signal.aborted) setBusy(false)
    }
  }

  async function sendImage(file: File) {
    if (busy) return
    const controller = new AbortController()
    abortRef.current = controller
    const url = URL.createObjectURL(file)
    objectUrls.current.push(url)
    const tempKey = `pending-${Date.now()}`
    setMessages((prev) => [
      ...prev,
      { key: tempKey, role: 'USER', type: 'IMAGE', content: '[이미지 분석 요청]', createdAt: new Date().toISOString(), items: [], imageUrl: url, imageName: file.name },
    ])
    setImage(null)
    setError(null)
    setBusy('image')
    try {
      const res = await api.sendImageQuery(file, activeId, controller.signal)
      setMessages((prev) => [
        ...prev,
        { key: res.messageId, role: 'ASSISTANT', type: 'IMAGE', content: res.answer, createdAt: new Date().toISOString(), items: [] },
      ])
      afterResponse(res.conversationId, '[이미지 분석 요청]')
    } catch (err) {
      if (controller.signal.aborted) return
      setMessages((prev) => prev.filter((m) => m.key !== tempKey))
      setImage(file)
      setError(err instanceof ApiError ? err.message : '이미지를 분석하지 못했습니다. 다시 시도해 주세요.')
    } finally {
      if (!controller.signal.aborted) setBusy(false)
    }
  }

  function submit() {
    if (image) void sendImage(image)
    else void sendText(text)
  }

  const isEmpty = messages.length === 0 && !busy && loadState === 'idle'
  const hasAnswer = messages.some((m) => m.role === 'ASSISTANT')

  return (
    <AppLayout>
      <div className="chat">
        {!isEmpty && (
          <header className="page-head">
            <div>
              <h1 className="page-head__title">{conversationTitle(title)}</h1>
              <p className="page-head__sub">대화가 내역에 자동으로 저장되어요</p>
            </div>
            {activeId && (
              <Link to={`/history/${activeId}`} className="btn btn--ghost btn--sm">
                <IconHistory size={16} /> 내역 보기
              </Link>
            )}
          </header>
        )}

        {!isEmpty && showNotice && (
          <div className="notice">
            <IconAlert size={16} />
            <span>AI 답변은 참고용이에요. 지원 전에 원문 공고에서 일정과 조건을 꼭 확인해 주세요.</span>
            <button type="button" className="icon-button" aria-label="안내 닫기" onClick={() => setShowNotice(false)}>
              <IconClose size={14} />
            </button>
          </div>
        )}

        <div className={`chat__scroll${isEmpty ? ' is-empty' : ''}`}>
          {isEmpty ? (
            <EmptyState name={user?.name} onPick={(q) => void sendText(q)} />
          ) : loadState === 'loading' ? (
            <div className="chat__status">대화를 불러오는 중…</div>
          ) : loadState === 'missing' ? (
            <div className="chat__status">
              <p>대화를 찾을 수 없어요. 삭제되었거나 다른 계정의 대화일 수 있어요.</p>
              <Link to="/chat" className="btn btn--primary btn--sm">
                새 대화 시작
              </Link>
            </div>
          ) : (
            <div className="chat__thread card">
              {messages.map((m, i) => (
                <div key={m.key}>
                  {(i === 0 || !isSameDay(messages[i - 1].createdAt, m.createdAt)) && <div className="day-divider">{formatDate(m.createdAt)}</div>}
                  {m.role === 'USER' ? <UserBubble message={m} /> : <AssistantBubble message={m} />}
                </div>
              ))}
              {busy && <TypingBubble image={busy === 'image'} />}
            </div>
          )}
        </div>

        <div className="chat__bottom">
          {hasAnswer && !busy && !image && (
            <div className="follow-ups">
              {FOLLOW_UPS.map((q) => (
                <button key={q} type="button" className="chip" onClick={() => void sendText(q)}>
                  {q}
                </button>
              ))}
            </div>
          )}
          {error && (
            <div className="alert alert--error" role="alert">
              <IconAlert size={16} /> {error}
              <button type="button" className="icon-button" aria-label="오류 닫기" onClick={() => setError(null)}>
                <IconClose size={14} />
              </button>
            </div>
          )}
          <Composer
            value={text}
            onChange={setText}
            image={image}
            onImageChange={setImage}
            onSubmit={submit}
            busy={!!busy}
            onError={setError}
          />
          <p className="disclaimer">AI 답변은 고용24·청년 일자리 지원 서비스의 공공데이터를 근거로 하지만, 실제 모집 조건은 원문에서 확인해 주세요.</p>
        </div>
      </div>
    </AppLayout>
  )
}
