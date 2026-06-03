import { ref } from 'vue'
import { formatDate } from '~/utils/format/date'
import { resetCustomerForm } from '~/composables/pos/helpers'

export function usePosCustomer() {
  const initial = resetCustomerForm()
  const customerType = ref(initial.customerType)
  const customerName = ref(initial.customerName)
  const customerPhone = ref(initial.customerPhone)
  const customerAddress = ref(initial.customerAddress)
  const source = ref(initial.source)
  const deliveryType = ref(initial.deliveryType)
  const deliveryPrice = ref(initial.deliveryPrice)
  const deliveryDate = ref(formatDate(new Date()))
  const paymentMethod = ref(initial.paymentMethod)
  const deliveryStatus = ref(initial.deliveryStatus)
  const sellerId = ref<number | undefined>(initial.sellerId)

  function reset() {
    const next = resetCustomerForm()
    customerType.value = next.customerType
    customerName.value = next.customerName
    customerPhone.value = next.customerPhone
    customerAddress.value = next.customerAddress
    source.value = next.source
    deliveryType.value = next.deliveryType
    deliveryPrice.value = next.deliveryPrice
    deliveryDate.value = formatDate(new Date())
    paymentMethod.value = next.paymentMethod
    deliveryStatus.value = next.deliveryStatus
    sellerId.value = next.sellerId
  }

  function applyInvoiceHeader(invoice: Record<string, unknown>) {
    customerName.value = String(invoice.customer || '')
    customerPhone.value = String(invoice.phoneCustomer || '')
    customerAddress.value = String(invoice.address || '')
    const src = String(invoice.source ?? '').trim()
    source.value = !src || src.toLowerCase() === 'other' ? 'Other' : src
    if (invoice.deliveryType) deliveryType.value = String(invoice.deliveryType)
    if (invoice.deliveryPrice != null) deliveryPrice.value = Number(invoice.deliveryPrice)
    if (invoice.deliveryDate) {
      const raw = String(invoice.deliveryDate)
      deliveryDate.value = raw.includes('T') ? formatDate(new Date(raw)) : raw
    }
    if (invoice.paymentMethod) paymentMethod.value = String(invoice.paymentMethod)
    if (invoice.deliveryStatus) deliveryStatus.value = String(invoice.deliveryStatus)
    const sid = invoice.sellerId
    sellerId.value = sid != null && sid !== '' ? Number(sid) : undefined
  }

  return {
    customerType,
    customerName,
    customerPhone,
    customerAddress,
    source,
    deliveryType,
    deliveryPrice,
    deliveryDate,
    paymentMethod,
    deliveryStatus,
    sellerId,
    reset,
    applyInvoiceHeader,
  }
}
