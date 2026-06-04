function formatWithTimeZone(
  datePayload: string | Date | number,
  options: Intl.DateTimeFormatOptions,
): string {
  if (!datePayload) return 'N/A'

  const d = new Date(datePayload)
  if (Number.isNaN(d.getTime())) {
    return String(datePayload)
  }

  const formatter = new Intl.DateTimeFormat('en-GB', {
    timeZone: 'Asia/Phnom_Penh',
    ...options,
  })

  const parts = formatter.formatToParts(d)
  const getPart = (type: string) => parts.find((p) => p.type === type)?.value || ''

  if (options.hour !== undefined) {
    return `${getPart('day')}/${getPart('month')}/${getPart('year')} ${getPart('hour')}:${getPart('minute')}`
  }

  return `${getPart('day')}/${getPart('month')}/${getPart('year')}`
}

/** dd/mm/yyyy (no time) — invoices, print previews. */
export const formatDateOnly = (datePayload: string | Date | number): string =>
  formatWithTimeZone(datePayload, {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })

export const formatDate = (datePayload: string | Date | number): string =>
  formatWithTimeZone(datePayload, {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  })
