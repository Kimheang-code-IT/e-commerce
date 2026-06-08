import type { FormField } from '~/types'

const KHMER_ALLOWED_REGEX = /^[\u1780-\u17FF\u19E0-\u19FF\s.,!?()\-/'":]+$/
const ENGLISH_ALLOWED_REGEX = /^[A-Za-z0-9\s@._,+!?()\-/'":]+$/
const NUMERIC_ALLOWED_REGEX = /^[0-9]+$/
const TEXT_ALLOWED_REGEX = /^[A-Za-z0-9\u1780-\u17FF\u19E0-\u19FF\s.,!?()\-/'":@._,+]+$/

export type TextRule = FormField['textRule']

const NON_TEXT_FIELD_TYPES = new Set([
  'number',
  'currency',
  'money-tabs',
  'select',
  'file',
  'date',
  'permission-tree',
  'password',
])

export function sanitizeKhmer(value: string): string {
  return value.replace(/[^\u1780-\u17FF\u19E0-\u19FF\s.,!?()\-/'":]/g, '')
}

export function sanitizeEnglish(value: string): string {
  return value.replace(/[^A-Za-z0-9\s@._,+!?()\-/'":]/g, '')
}

export function sanitizeText(value: string): string {
  return value.replace(/[^A-Za-z0-9\u1780-\u17FF\u19E0-\u19FF\s.,!?()\-/'":@._,+]/g, '')
}

export function sanitizeByTextRule(rule: TextRule, value: string): string {
  if (!rule) return value
  if (rule === 'khmer') return sanitizeKhmer(value)
  if (rule === 'english') return sanitizeText(value)
  if (rule === 'numeric') return value.replace(/\D/g, '')
  if (rule === 'text') return sanitizeText(value)
  return value
}

export function isValidByTextRule(rule: TextRule, value: string): boolean {
  if (!rule) return true
  if (!value.trim()) return true
  if (rule === 'khmer') return KHMER_ALLOWED_REGEX.test(value)
  if (rule === 'english') return TEXT_ALLOWED_REGEX.test(value)
  if (rule === 'numeric') return NUMERIC_ALLOWED_REGEX.test(value)
  if (rule === 'text') return TEXT_ALLOWED_REGEX.test(value)
  return true
}

export function resolveTextRule(field: Pick<FormField, 'type' | 'textRule' | 'key'>): TextRule | undefined {
  if (field.textRule) return field.textRule
  const type = field.type || 'input'
  if (NON_TEXT_FIELD_TYPES.has(type)) return undefined
  if (field.key === 'email') return undefined
  if (type === 'input' || type === 'textarea') return 'text'
  return undefined
}

export function textRuleErrorMessage(field: Pick<FormField, 'key' | 'label' | 'textRule' | 'type'>, value: string): string {
  const rule = resolveTextRule(field)
  if (!rule || isValidByTextRule(rule, value)) return ''
  const label = field.label || field.key
  if (rule === 'khmer') return `${label} must contain Khmer only.`
  if (rule === 'numeric') return `${label} must contain numbers only.`
  return `${label} must contain text only.`
}

export function resolveCurrencyPrefix(field: Pick<FormField, 'currencyPrefix'>): string {
  return field.currencyPrefix || 'USD'
}
