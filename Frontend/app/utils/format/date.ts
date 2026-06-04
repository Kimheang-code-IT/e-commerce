export const formatDate = (datePayload: string | Date | number): string => {
  if (!datePayload) return 'N/A'

  const d = new Date(datePayload)
  if (Number.isNaN(d.getTime())) {
    return String(datePayload)
  }

  // Use Intl.DateTimeFormat to force Cambodia/ICT time (UTC+7)
  const formatter = new Intl.DateTimeFormat('en-GB', {
    timeZone: 'Asia/Phnom_Penh',
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  })

  const parts = formatter.formatToParts(d)
  const getPart = (type: string) => parts.find(p => p.type === type)?.value || ''

  return `${getPart('day')}/${getPart('month')}/${getPart('year')} ${getPart('hour')}:${getPart('minute')}`
}

/** Invoice / display date without time — dd/mm/yyyy (Asia/Phnom_Penh). */
export const formatDateOnly = (datePayload: string | Date | number): string => {
  if (!datePayload) return 'N/A'

  const normalized = String(datePayload).trim()
  const dateOnlyMatch = normalized.match(/^(\d{2})\/(\d{2})\/(\d{4})/)
  if (dateOnlyMatch) {
    return `${dateOnlyMatch[1]}/${dateOnlyMatch[2]}/${dateOnlyMatch[3]}`
  }

  const d = new Date(datePayload)
  if (Number.isNaN(d.getTime())) {
    return normalized
  }

  const formatter = new Intl.DateTimeFormat('en-GB', {
    timeZone: 'Asia/Phnom_Penh',
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })

  const parts = formatter.formatToParts(d)
  const getPart = (type: string) => parts.find((p) => p.type === type)?.value || ''

  return `${getPart('day')}/${getPart('month')}/${getPart('year')}`
}
