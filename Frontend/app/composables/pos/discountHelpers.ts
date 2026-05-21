export type DiscountMode = 'usd' | 'percent'

export function discountUsdFromInput(
  mode: DiscountMode,
  input: number,
  subtotal: number
): number {
  const sub = Math.max(0, subtotal)
  if (mode === 'percent') {
    const pct = Math.min(100, Math.max(0, Number(input) || 0))
    return Math.round(((sub * pct) / 100) * 100) / 100
  }
  return Math.min(sub, Math.max(0, Number(input) || 0))
}

export type DiscountValidationKey = 'invalid' | 'percentMax' | 'usdMax'

export function validateDiscountInput(
  mode: DiscountMode,
  input: number,
  subtotal: number
): DiscountValidationKey | null {
  const v = Number(input)
  if (!Number.isFinite(v) || v < 0) return 'invalid'
  if (mode === 'percent' && v > 100) return 'percentMax'
  if (mode === 'usd' && subtotal >= 0 && v > subtotal) return 'usdMax'
  return null
}
