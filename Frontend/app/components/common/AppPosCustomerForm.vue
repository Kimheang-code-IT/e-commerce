<script setup lang="ts">
import { formatDate } from '~/utils/format/date'

const customerType = defineModel<string>('customerType', { required: true })
const customerName = defineModel<string>('customerName', { required: true })
const customerPhone = defineModel<string>('customerPhone', { required: true })
const customerAddress = defineModel<string>('customerAddress', { required: true })
const deliveryType = defineModel<string>('deliveryType', { required: true })
const deliveryPrice = defineModel<number>('deliveryPrice', { required: true })
const deliveryDate = defineModel<string>('deliveryDate', { required: true })
const paymentMethod = defineModel<string>('paymentMethod', { required: true, default: 'cash' })
const deliveryStatus = defineModel<string>('deliveryStatus', { required: true, default: 'pending' })
const source = defineModel<string>('source', { required: true, default: 'other' })
const sellerId = defineModel<number | undefined>('sellerId')
const { t } = useI18n()
const auth = useAuthStore()
const sellerName = computed(() => String(auth.user?.name || ''))
const sellerRole = computed(() => String(auth.user?.role || '').toLowerCase())
watch(
  () => auth.user,
  (u) => {
    const rawId = Number((u as any)?.id)
    sellerId.value = Number.isFinite(rawId) && rawId > 0 ? rawId : undefined
  },
  { immediate: true, deep: true }
)
const deliveryDatePart = ref('')
const deliveryTimePart = ref('')

const customerTypes = [t('pages.pos.customer.types.customer'), t('pages.pos.customer.types.walkIn')]
const deliveryTypeItems = [
  t('pages.pos.customer.form.deliveryTypeVET'),
  t('pages.pos.customer.form.deliveryTypeDomnaksiiksa'),
  t('pages.pos.customer.form.deliveryTypeGrap'),
  t('pages.pos.customer.form.deliveryTypeJNT')
]
const paymentMethodItems = [
  { label: t('pages.pos.customer.form.paymentCash'), value: 'cash' },
  { label: t('pages.pos.customer.form.paymentAcleda'), value: 'acleda' },
  { label: t('pages.pos.customer.form.paymentABA'), value: 'aba' },
  { label: t('pages.pos.customer.form.paymentWing'), value: 'wing' },
  { label: t('pages.pos.customer.form.paymentOther'), value: 'other' }
]
const deliveryStatusItems = [
  { label: t('pages.pos.customer.form.statusPending'), value: 'pending' },
  { label: t('pages.pos.customer.form.statusDelivered'), value: 'delivered' }
]
const sourceItems = [
  t('pages.pos.customer.form.sourceDomnaksiiksa'),
  t('pages.pos.customer.form.sourceLearnFast'),
  t('pages.pos.customer.form.sourceReanChinese'),
  t('pages.pos.customer.form.sourceOther')
]
const customerTypeTabs = computed(() => [
  { label: t('pages.pos.customer.types.customer'), value: 'Customer' },
  { label: t('pages.pos.customer.types.walkIn'), value: 'walkIn' }
])
const provinceNames = [
  'Phnom Penh',
  'Siemreap',
  'Preah Sihanouk',
  'Battambang',
  'Kampong Cham',
  'Kandal',
  'Banteay Meanchey',
  'Kampong Speu',
  'Prey Veng',
  'Kampot',
  'Takeo',
  'Kampong Thom',
  'Pursat',
  'Tboung Khmum',
  'Kratie',
  'Svay Rieng',
  'Mondul Kiri',
  'Ratanak Kiri',
  'Stung Treng',
  'Oddar Meanchey',
  'Kep',
  'Pailin',
  'Preah Vihear',
  'Koh Kong'
]
const provinceItems = [
  t('common.nothing'),
  ...provinceNames.map(name => t('provinces.' + name))
]

function onSelectCustomerType(type: string) {
  customerType.value = type

  if (type === 'walkIn') {
    customerName.value = 'Walk-in'
    customerPhone.value = '000000000'
    customerAddress.value = 'Nothing'
    return
  }

  customerName.value = ''
  customerPhone.value = ''
  customerAddress.value = ''
}

watch(customerType, (type) => {
  if (!type) return
  onSelectCustomerType(type)
})

if (!deliveryType.value) {
  deliveryType.value = deliveryTypeItems[0] as string
}

if (deliveryPrice.value === undefined || deliveryPrice.value === null || Number.isNaN(Number(deliveryPrice.value))) {
  deliveryPrice.value = 2
}
if (!source.value) {
  source.value = 'other'
}

function pad(value: number): string {
  return String(value).padStart(2, '0')
}

function toDisplayDate(value: Date): string {
  // Use Intl.DateTimeFormat to get parts in Asia/Phnom_Penh
  const formatter = new Intl.DateTimeFormat('en-GB', {
    timeZone: 'Asia/Phnom_Penh',
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  })
  const parts = formatter.formatToParts(value)
  const get = (t: string) => parts.find(p => p.type === t)?.value || '00'
  return `${get('day')}/${get('month')}/${get('year')} ${get('hour')}:${get('minute')}:${get('second')}`
}

function parseDisplayDate(value: string): Date | null {
  const normalized = String(value || '').trim()
  const match = normalized.match(/^(\d{2})\/(\d{2})\/(\d{4}) (\d{2}):(\d{2})(?::(\d{2}))?$/)
  if (!match) return null
  const [, dd, mm, yyyy, hh, min, sec] = match
  
  // Create a UTC date string that matches Cambodia time
  // e.g. "2024-05-05T12:00:00+07:00"
  const isoStr = `${yyyy}-${mm}-${dd}T${hh}:${min}:${sec || '00'}+07:00`
  const date = new Date(isoStr)
  return Number.isNaN(date.getTime()) ? null : date
}

function syncPartsFromModel() {
  const parsed = parseDisplayDate(deliveryDate.value)
  const date = parsed || new Date()
  
  // Format for input[type="date"] and input[type="time"]
  // These should be formatted in Cambodia time too
  const formatter = new Intl.DateTimeFormat('en-GB', {
    timeZone: 'Asia/Phnom_Penh',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  })
  const p = formatter.formatToParts(date)
  const g = (t: string) => p.find(x => x.type === t)?.value || '00'
  
  deliveryDatePart.value = `${g('year')}-${g('month')}-${g('day')}`
  deliveryTimePart.value = `${g('hour')}:${g('minute')}`
}

function syncModelFromParts() {
  if (!deliveryDatePart.value || !deliveryTimePart.value) return
  const dateParts = deliveryDatePart.value.split('-').map(Number)
  const timeParts = deliveryTimePart.value.split(':').map(Number)
  
  if (dateParts.length < 3 || timeParts.length < 2) return
  const [yyyy, mm, dd] = dateParts as [number, number, number]
  const [hh, min] = timeParts as [number, number]
  
  if (Number.isNaN(yyyy) || Number.isNaN(mm) || Number.isNaN(dd) || Number.isNaN(hh) || Number.isNaN(min)) return
  
  // Construct date as if it were in Cambodia
  const isoStr = `${pad(yyyy)}-${pad(mm)}-${pad(dd)}T${pad(hh)}:${pad(min)}:00+07:00`
  const date = new Date(isoStr)
  deliveryDate.value = toDisplayDate(date)
}

if (!deliveryDate.value) {
  deliveryDate.value = toDisplayDate(new Date())
}

syncPartsFromModel()

watch(deliveryDate, () => {
  syncPartsFromModel()
})

watch([deliveryDatePart, deliveryTimePart], () => {
  syncModelFromParts()
})
</script>

<template>
  <div class="w-full flex flex-col px-6 py-2 lg:px-8 bg-card overflow-y-auto lg:border-r border-default">
    <div class="max-w-2xl mx-auto w-full space-y-4">
      <div class="w-full">
        <UTabs
          v-model="customerType"
          :items="customerTypeTabs"
          :content="false"
          color="primary"
          class="w-full"
        />
      </div>

      <div class="flex flex-col w-full gap-3">
        <div class="flex flex-col sm:flex-row gap-3 w-full">
          <div class="flex-1 space-y-1.5">
            <label class="text-sm text-muted-foreground">
              {{ $t('pages.pos.customer.form.name') }} <span class="text-error">*</span>
            </label>
            <UInput v-model="customerName" :placeholder="$t('pages.pos.customer.form.namePlaceholder')" size="lg" class="w-full mt-1" />
          </div>
          <div class="flex-1 space-y-1.5">
            <label class="text-sm text-muted-foreground">
              {{ $t('pages.pos.customer.form.phone') }} <span class="text-error">*</span>
            </label>
            <UInput v-model="customerPhone" :placeholder="$t('pages.pos.customer.form.phonePlaceholder')" size="lg" class="w-full mt-1" />
          </div>
        </div>
        <div class="flex flex-col sm:flex-row gap-3 w-full">
          <div class="flex-1 space-y-1.5">
            <label class="text-sm text-muted-foreground">{{ $t('pages.pos.customer.form.deliveryType') }}<span class="text-error ml-1">*</span></label>
            <USelect
              v-model="deliveryType"
              :items="deliveryTypeItems"
              size="lg"
              class="w-full mt-1"
            />
          </div>
          <div class="flex-1 space-y-1.5">
            <label class="text-sm text-muted-foreground">{{ $t('pages.pos.customer.form.deliveryPrice') }}<span class="text-error ml-1">*</span></label>
            <UInput
              v-model.number="deliveryPrice"
              type="number"
              min="0"
              step="0.01"
              size="lg"
              class="w-full mt-1"
            />
          </div>
        </div>
        <div class="space-y-1.5">
          <label class="text-sm text-muted-foreground">{{ $t('pages.pos.customer.form.deliveryDate') }} <span class="text-error">*</span></label>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-1">
            <UInput
              v-model="deliveryDatePart"
              type="date"
              size="lg"
              class="w-full"
            />
            <UInput
              v-model="deliveryTimePart"
              type="time"
              size="lg"
              class="w-full"
            />
          </div>
        </div>

        <div class="flex flex-col sm:flex-row gap-3 w-full">
          <div class="flex-1 space-y-1.5">
            <label class="text-sm text-muted-foreground">{{ $t('pages.pos.customer.form.paymentMethod') }} <span class="text-error">*</span></label>
            <USelect
              v-model="paymentMethod"
              :items="paymentMethodItems"
              size="lg"
              class="w-full mt-1"
            />
          </div>
          <div class="flex-1 space-y-1.5">
            <label class="text-sm text-muted-foreground">{{ $t('pages.pos.customer.form.deliveryStatus') }}<span class="text-error">*</span></label>
            <USelect
              v-model="deliveryStatus"
              :items="deliveryStatusItems"
              size="lg"
              class="w-full mt-1"
            />
          </div>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full">
          <div class="flex-1 space-y-1.5">
            <label class="text-sm text-muted-foreground">{{ $t('pages.pos.customer.form.source') }} <span class="text-error">*</span></label>
            <USelect
              v-model="source"
              :items="sourceItems"
              size="lg"
              class="w-full mt-1"
            />
          </div>
          <div class="space-y-1.5">
            <label class="text-sm text-muted-foreground">{{ $t('pages.pos.customer.form.address') }}<span class="text-error ml-1">*</span></label>
            <USelectMenu
              v-model="customerAddress"
              :items="provinceItems"
              searchable
              :placeholder="$t('pages.pos.customer.form.addressPlaceholder')"
              size="lg"
              class="w-full mt-1"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
