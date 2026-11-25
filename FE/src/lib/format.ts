const timeFormat = new Intl.DateTimeFormat('ko-KR', { hour: 'numeric', minute: '2-digit' })
const dateFormat = new Intl.DateTimeFormat('ko-KR', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'short' })
const shortDate = new Intl.DateTimeFormat('ko-KR', { month: 'long', day: 'numeric' })

function toDate(value: string | Date) {
  return value instanceof Date ? value : new Date(value)
}

export function formatTime(value: string | Date) {
  return timeFormat.format(toDate(value))
}

export function formatDate(value: string | Date) {
  return dateFormat.format(toDate(value))
}

export function formatDotDate(value: string | Date) {
  const d = toDate(value)
  return `${d.getFullYear()}.${String(d.getMonth() + 1).padStart(2, '0')}.${String(d.getDate()).padStart(2, '0')}`
}

export function isSameDay(a: string | Date, b: string | Date) {
  const x = toDate(a)
  const y = toDate(b)
  return x.getFullYear() === y.getFullYear() && x.getMonth() === y.getMonth() && x.getDate() === y.getDate()
}

/** 목록용: 오늘이면 "오늘 · 오후 2:32", 아니면 "10월 18일 · 오후 2:32" */
export function formatListStamp(value: string) {
  const prefix = isSameDay(value, new Date()) ? '오늘' : shortDate.format(toDate(value))
  return `${prefix} · ${formatTime(value)}`
}

export function conversationTitle(title: string | null | undefined) {
  return title?.trim() || '새 대화'
}
