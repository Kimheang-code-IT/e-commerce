import type { Row } from '@tanstack/vue-table'
import type { CommissionEntry } from '~/types'

export function commissionLineQty(row: CommissionEntry): number {
  const qty = Number(row.qty ?? 0)
  return qty > 0 ? qty : 1
}

export function sumCommissionRows(rows: CommissionEntry[]): {
  productCount: number
  commissionTotal: number
  amountTotal: number
} {
  return rows.reduce(
    (acc, row) => ({
      productCount: acc.productCount + commissionLineQty(row),
      commissionTotal: acc.commissionTotal + Number(row.commission || 0),
      amountTotal: acc.amountTotal + Number(row.amount || 0),
    }),
    { productCount: 0, commissionTotal: 0, amountTotal: 0 },
  )
}

export function aggregateCommissionTableRow(
  row: Row<CommissionEntry>,
): { productCount: number; commissionTotal: number } {
  if (row.getIsGrouped()) {
    const leaves: CommissionEntry[] = []
    const walk = (sub: Row<CommissionEntry>) => {
      if (sub.getIsGrouped()) {
        sub.subRows?.forEach(walk)
        return
      }
      if (sub.original) leaves.push(sub.original)
    }
    row.subRows?.forEach(walk)
    return sumCommissionRows(leaves)
  }

  const entry = row.original
  return {
    productCount: entry ? commissionLineQty(entry) : 0,
    commissionTotal: Number(entry?.commission || 0),
  }
}
