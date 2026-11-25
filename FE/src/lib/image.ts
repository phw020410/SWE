export const MAX_QUERY_LENGTH = 1000
export const MAX_IMAGE_BYTES = 5 * 1024 * 1024
const IMAGE_TYPES = ['image/jpeg', 'image/png']

/** FR-004 / ERR-007: JPG·PNG, 5MB 이하만 허용 (서버도 다시 검사함) */
export function validateImageFile(file: File): string | null {
  const ext = file.name.toLowerCase().split('.').pop() ?? ''
  if (!IMAGE_TYPES.includes(file.type) || !['jpg', 'jpeg', 'png'].includes(ext)) return 'JPG, PNG 이미지만 올릴 수 있어요.'
  if (file.size > MAX_IMAGE_BYTES) return '5MB 이하 이미지만 올릴 수 있어요.'
  return null
}
