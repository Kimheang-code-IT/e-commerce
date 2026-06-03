import { computed } from 'vue'
import { buildCambodiaProvinceSelectItems } from '~/utils/provinces'

/** Fixed POS customer fields — only these values can be selected. */
export const POS_DELIVERY_TYPES = ['VET', 'Grap', 'J&T', 'Other'] as const
export const POS_PAYMENT_METHODS = ['cash', 'acleda', 'aba', 'wing', 'other'] as const

export const POS_WALK_IN_DELIVERY_TYPE = 'Other'
export const POS_WALK_IN_SOURCE = 'Other'
export const POS_WALK_IN_ADDRESS = 'Nothing'

export type PosSelectItem = { label: string; value: string }

const PAYMENT_LABELS: Record<string, string> = {
  cash: 'Cash',
  acleda: 'ACLEDA Bank',
  aba: 'ABA Bank',
  wing: 'Wing',
  other: 'Other'
}

const DELIVERY_TYPE_I18N: Record<(typeof POS_DELIVERY_TYPES)[number], string> = {
  VET: 'pages.pos.customer.form.deliveryTypeVET',
  Grap: 'pages.pos.customer.form.deliveryTypeGrap',
  'J&T': 'pages.pos.customer.form.deliveryTypeJNT',
  Other: 'pages.pos.customer.form.deliveryTypeOther',
}

function toSelectItems(values: readonly string[], labels?: Record<string, string>) {
  return values.map((value) => ({
    value,
    label: labels?.[value] ?? labels?.[value.toLowerCase()] ?? value
  }))
}

export function usePosFormOptions() {
  const { t } = useI18n()

  const deliveryTypeItems = computed<PosSelectItem[]>(() =>
    POS_DELIVERY_TYPES.map((value) => ({
      value,
      label: t(DELIVERY_TYPE_I18N[value]),
    })),
  )
  const paymentMethodItems = computed(() => toSelectItems(POS_PAYMENT_METHODS, PAYMENT_LABELS))
  const addressItems = computed(() => buildCambodiaProvinceSelectItems((key) => t(key)))

  return {
    deliveryTypeItems,
    paymentMethodItems,
    addressItems
  }
}
