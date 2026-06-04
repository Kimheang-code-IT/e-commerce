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
