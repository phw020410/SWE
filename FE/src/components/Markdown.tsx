import DOMPurify from 'dompurify'
import { marked } from 'marked'
import { useMemo } from 'react'

// 링크는 새 탭에서 열고, 원래 페이지 정보를 넘기지 않는다.
DOMPurify.addHook('afterSanitizeAttributes', (node) => {
  if (node.tagName === 'A') {
    node.setAttribute('target', '_blank')
    node.setAttribute('rel', 'noopener noreferrer')
  }
})

marked.setOptions({ gfm: true, breaks: true })

/** AI 응답 Markdown을 DOMPurify로 정리한 뒤 렌더링한다 (SDD 9장: XSS 방지). */
function renderMarkdown(source: string) {
  const html = marked.parse(source, { async: false })
  // 외부 이미지·폼·스타일은 AI 응답에 필요 없으므로 막는다 (추적 픽셀, 레이아웃 깨짐 방지)
  return DOMPurify.sanitize(html, { USE_PROFILES: { html: true }, FORBID_TAGS: ['img', 'style', 'form', 'input', 'button', 'iframe'] })
}

export function Markdown({ source, className = '' }: { source: string; className?: string }) {
  const html = useMemo(() => renderMarkdown(source), [source])
  return <div className={`markdown ${className}`} dangerouslySetInnerHTML={{ __html: html }} />
}
