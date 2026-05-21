import { computed } from 'vue'
import { buildCambodiaProvinceSelectItems } from '~/utils/provinces'

/** Fixed POS customer fields — only these values can be selected. */
export const POS_DELIVERY_TYPES = ['VET', 'Domnaksiiksa', 'Grap', 'J&T', 'Other'] as const
export const POS_SOURCES = ['Domnaksiiksa', 'Learn fast', 'rean chinese', 'Other'] as const
export const POS_PAYMENT_METHODS = ['cash', 'acleda', 'aba', 'wing', 'other'] as const

export const POS_WALK_IN_DELIVERY_TYPE = 'Other'
export const POS_WALK_IN_SOURCE = 'Other'
export const POS_WALK_IN_ADDRESS = 'Nothing'

const PAYMENT_LABELS: Record<string, string> = {
  cash: 'Cash',
  acleda: 'ACLEDA Bank',
  aba: 'ABA Bank',
  wing: 'Wing',
  other: 'Other'
}

function toSelectItems(values: readonly string[], labels?: Record<string, string>) {
  return values.map((value) => ({
    value,
    label: labels?.[value] ?? labels?.[value.toLowerCase()] ?? value
  }))
}

export function usePosFormOptions() {
  const { t } = useI18n()

  const deliveryTypeItems = computed(() => toSelectItems(POS_DELIVERY_TYPES))
  const sourceItems = computed(() => toSelectItems(POS_SOURCES))
  const paymentMethodItems = computed(() => toSelectItems(POS_PAYMENT_METHODS, PAYMENT_LABELS))
  const addressItems = computed(() => buildCambodiaProvinceSelectItems((key) => t(key)))

  return {
    deliveryTypeItems,
    sourceItems,
    paymentMethodItems,
    addressItems
  }
}
