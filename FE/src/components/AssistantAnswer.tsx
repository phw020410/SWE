import { useState } from 'react'
import type { RecommendedItem } from '../api/types'
import { ItemCards } from './ItemCards'
import { Markdown } from './Markdown'

/**
 * AI 응답 표시.
 * 추천 항목(items)이 있으면 Markdown의 첫 소개 문단 + 카드로 보여 주고,
 * 전체 Markdown 원문은 접어서 볼 수 있게 한다.
 */
export function AssistantAnswer({ content, items }: { content: string; items: RecommendedItem[] }) {
  const [showFull, setShowFull] = useState(false)

  if (!items.length) return <Markdown source={content} />

  const intro = content.split(/\n#{2,3}\s/)[0]
  return (
    <div className="answer">
      <Markdown source={intro} />
      <ItemCards items={items} />
      <p className="answer__note">지원 가능 여부와 상세 일정·조건은 원문에서 최종 확인해 주세요.</p>
      <button type="button" className="link-button" onClick={() => setShowFull((v) => !v)} aria-expanded={showFull}>
        {showFull ? '상세 정보 접기' : '상세 정보 펼치기 (Markdown)'}
      </button>
      {showFull && (
        <div className="answer__full">
          <Markdown source={content} />
        </div>
      )}
    </div>
  )
}
