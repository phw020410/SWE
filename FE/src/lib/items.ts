import type { RecommendedItem } from '../api/types'

/**
 * 추천 항목 형식 통일.
 * - /api/query 응답: region·starts_at 등이 최상위에 있고 raw_data는 원천 부가 필드
 * - /api/history 응답: DB의 raw_data 컬럼에 항목 전체 스냅샷이 들어 있어 raw_data.raw_data 가 원천 부가 필드
 */
export function normalizeItem(item: RecommendedItem): RecommendedItem {
  const raw = item.raw_data as Record<string, unknown> | undefined
  if (raw && typeof raw === 'object' && 'item_type' in raw && 'external_id' in raw) {
    const snapshot = raw as unknown as RecommendedItem
    return { ...snapshot, ...stripUndefined(item), raw_data: (snapshot.raw_data ?? {}) as Record<string, unknown> }
  }
  return item
}

function stripUndefined(item: RecommendedItem) {
  const out: Partial<RecommendedItem> = {}
  for (const [key, value] of Object.entries(item)) {
    if (value !== undefined && value !== null && key !== 'raw_data') (out as Record<string, unknown>)[key] = value
  }
  return out
}
