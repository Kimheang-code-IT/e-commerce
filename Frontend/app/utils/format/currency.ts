const USDFormatter = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  minimumFractionDigits: 2,
  maximumFractionDigits: 2
})

const KHRFormatter = new Intl.NumberFormat('en-US', {
  style: 'decimal',
  minimumFractionDigits: 0,
  maximumFractionDigits: 0
})

const NumberFormatter = new Intl.NumberFormat('en-US')

export const formatCurrency = (amount: number | null | undefined, currency: 'USD' | 'KHR' = 'USD'): string => {
  if (amount === null || amount === undefined || isNaN(amount)) return currency === 'USD' ? '$0.00' : '0 ៛'
  if (currency === 'KHR') return `${KHRFormatter.format(amount)} ៛`
  return USDFormatter.format(amount)
}

export const formatNumber = (num: number | null | undefined): string => {
  if (num === null || num === undefined || isNaN(num)) return '0'
  return NumberFormatter.format(num)
}
