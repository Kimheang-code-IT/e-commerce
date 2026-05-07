/**
 * Universal generic components mapped to `helpers/common.ts` 
 */

export const exportToCSV = (data: any[], filename: string = 'export.csv') => {
  if (!data || !data.length) return

  const headers = Object.keys(data[0])
  const csvContent = [
    headers.join(','),
    ...data.map(row => 
      headers.map(field => {
        let val = row[field]
        if (val === null || val === undefined) val = ''
        const str = String(val)
        return str.includes(',') ? `"${str}"` : str
      }).join(',')
    )
  ].join('\n')

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  
  if (typeof window !== 'undefined') {
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }
}

export const getActionColor = (type: string): 'success' | 'warning' | 'error' | 'info' | 'primary' | 'neutral' => {
  switch (type.toLowerCase()) {
      case 'create':
      case 'add':          return 'success'
      case 'update':
      case 'edit':         return 'warning'
      case 'delete':
      case 'remove':       return 'error'
      case 'login':        return 'info'
      case 'export':
      case 'download':     return 'primary'
      case 'logout':
      default:             return 'neutral'
  }
}
