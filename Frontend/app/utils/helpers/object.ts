export const safeClone = <T>(obj: T): T => {
  if (!obj) return obj
  return JSON.parse(JSON.stringify(obj))
}
