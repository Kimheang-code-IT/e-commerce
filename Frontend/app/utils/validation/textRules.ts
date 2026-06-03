import type { FormField } from '~/types'

const KHMER_ALLOWED_REGEX = /^[\u1780-\u17FF\u19E0-\u19FF\s.,!?()\-/'":]+$/
const ENGLISH_ALLOWED_REGEX = /^[A-Za-z0-9\s@._,+!?()\-/'":]+$/
const NUMERIC_ALLOWED_REGEX = /^[0-9]+$/
const TEXT_ALLOWED_REGEX = /^[A-Za-z\u1780-\u17FF\u19E0-\u19FF\s.,!?()\-/'":]+$/

export type TextRule = FormField['textRule']

export function sanitizeKhmer(value: string): string {
  return value.replace(/[^\u1780-\u17FF\u19E0-\u19FF\s.,!?()\-/'":]/g, '')
}

export function sanitizeEnglish(value: string): string {
  return value.replace(/[^A-Za-z0-9\s@._,+!?()\-/'":]/g, '')
}

export function sanitizeByTextRule(rule: TextRule, value: string): string {
  if (!rule) return value
  if (rule === 'khmer') return sanitizeKhmer(value)
  if (rule === 'english') return sanitizeEnglish(value)
  if (rule === 'numeric') return value.replace(/\D/g, '')
  if (rule === 'text') return value.replace(/[^A-Za-z\u1780-\u17FF\u19E0-\u19FF\s.,!?()\-/'":]/g, '')
  return value
}

export function isValidByTextRule(rule: TextRule, value: string): boolean {
  if (!rule) return true
  if (!value.trim()) return true
  if (rule === 'khmer') return KHMER_ALLOWED_REGEX.test(value)
  if (rule === 'english') return ENGLISH_ALLOWED_REGEX.test(value)
  if (rule === 'numeric') return NUMERIC_ALLOWED_REGEX.test(value)
  if (rule === 'text') return TEXT_ALLOWED_REGEX.test(value)
  return true
}

export function textRuleErrorMessage(field: Pick<FormField, 'key' | 'label' | 'textRule'>, value: string): string {
  const label = field.label || field.key
  if (!isValidByTextRule(field.textRule, value)) {
    if (field.textRule === 'khmer') return `${label} must contain Khmer only.`
    if (field.textRule === 'english') return `${label} must contain English only.`
    if (field.textRule === 'numeric') return `${label} must contain numbers only.`
    if (field.textRule === 'text') return `${label} must contain text only.`
  }
  return ''
}

export function resolveCurrencyPrefix(field: Pick<FormField, 'currencyPrefix'>): string {
  return field.currencyPrefix || 'USD'
}
