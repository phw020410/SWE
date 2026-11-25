// localStorage는 사생활 보호 모드 등에서 예외를 던질 수 있어 항상 감싸서 사용한다.

export function readJson<T>(key: string): T | null {
  try {
    const raw = window.localStorage.getItem(key)
    return raw ? (JSON.parse(raw) as T) : null
  } catch {
    return null
  }
}

export function writeJson(key: string, value: unknown) {
  try {
    window.localStorage.setItem(key, JSON.stringify(value))
  } catch {
    // 저장 실패 시 메모리 상태만 유지
  }
}

export function remove(key: string) {
  try {
    window.localStorage.removeItem(key)
  } catch {
    // 무시
  }
}
