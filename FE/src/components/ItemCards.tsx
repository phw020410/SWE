import type { RecommendedItem } from '../api/types'
import { normalizeItem } from '../lib/items'
import { IconBriefcase, IconExternal, IconGraduation } from './Icons'

const SOURCE_LABEL: Record<string, string> = {
  WORK24: '고용24',
  YOUTH_JOB: '청년 일자리 지원 서비스',
}

function safeUrl(url: string | null | undefined) {
  if (!url) return null
  try {
    const parsed = new URL(url)
    return parsed.protocol === 'https:' || parsed.protocol === 'http:' ? parsed.href : null
  } catch {
    return null
  }
}

function ItemCard({ item }: { item: RecommendedItem }) {
  const isTraining = item.item_type === 'TRAINING'
  const url = safeUrl(item.url)
  const extras = Object.entries(item.raw_data ?? {})
    .filter(([key, value]) => value && key !== '안내' && typeof value !== 'object')
    .slice(0, 3)

  return (
    <article className="item-card">
      <div className="item-card__head">
        <span className={`item-card__icon ${isTraining ? 'is-training' : 'is-job'}`}>
          {isTraining ? <IconGraduation size={18} /> : <IconBriefcase size={18} />}
        </span>
        <span className={`badge ${isTraining ? 'badge--teal' : 'badge--amber'}`}>{isTraining ? '교육·훈련' : '채용'}</span>
      </div>
      <h4 className="item-card__title">{item.title}</h4>
      <p className="item-card__org">{item.organization}</p>
      <ul className="item-card__meta">
        {item.region && <li>{item.region}</li>}
        {item.starts_at && <li>시작 {item.starts_at}</li>}
        {item.ends_at && <li>마감 {item.ends_at}</li>}
        {extras.map(([key, value]) => (
          <li key={key}>
            {key} {String(value)}
          </li>
        ))}
      </ul>
      <div className="item-card__foot">
        <span className="item-card__source">출처: {SOURCE_LABEL[item.source] ?? item.source}</span>
        {url ? (
          <a href={url} target="_blank" rel="noopener noreferrer" className="item-card__link">
            원문 보기 <IconExternal size={14} />
          </a>
        ) : (
          <span className="item-card__source">원문 링크 미제공</span>
        )}
      </div>
    </article>
  )
}

export function ItemCards({ items: input }: { items: RecommendedItem[] }) {
  const items = input.map(normalizeItem)
  const groups: { type: RecommendedItem['item_type']; label: string }[] = [
    { type: 'TRAINING', label: '추천 교육·훈련' },
    { type: 'JOB', label: '함께 살펴볼 채용' },
  ]
  return (
    <div className="item-groups">
      {groups.map(({ type, label }) => {
        const group = items.filter((x) => x.item_type === type)
        if (!group.length) return null
        return (
          <section key={type} className="item-group">
            <h3 className="item-group__title">
              {label} <span>{group.length}건</span>
            </h3>
            <div className="item-grid">
              {group.map((item) => (
                <ItemCard key={`${item.source}-${item.external_id}`} item={item} />
              ))}
            </div>
          </section>
        )
      })}
    </div>
  )
}
