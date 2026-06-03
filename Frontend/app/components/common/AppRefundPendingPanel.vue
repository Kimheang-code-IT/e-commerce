<script setup lang="ts">
import { watch } from 'vue'
import { formatCurrency } from '~/utils/format/currency'
import type { ReportRow } from '~/types'
import { sanitizeKhmer } from '~/utils/validation/textRules'

const refundReason = defineModel<string>('reason', { default: '' })

defineProps<{
  invoiceNo: string
  rows: ReportRow[]
  selectedIds: Set<number>
  loading?: boolean
  submitting?: boolean
}>()

const emit = defineEmits<{
  (e: 'confirm'): void
  (e: 'cancel'): void
  (e: 'toggle-row', id: number, checked: boolean): void
}>()

const { t } = useI18n()

watch(refundReason, (value) => {
  const sanitized = sanitizeKhmer(String(value || ''))
  if (sanitized !== value) refundReason.value = sanitized
})

function isSelected(id: number | undefined, selectedIds: Set<number>) {
  return id != null && selectedIds.has(Number(id))
}
</script>

<template>
  <div class="rounded-lg border border-default bg-muted/20 p-3 space-y-3 shrink-0">
    <div class="flex items-center gap-2">
      <h3 class="font-semibold text-sm mr-auto">
        {{ t('pages.refund.pending.title') }}
        <span class="text-primary ml-1">{{ invoiceNo }}</span>
      </h3>
      <UButton
        icon="i-lucide-x"
        color="neutral"
        variant="ghost"
        size="xs"
        :disabled="submitting"
        @click="emit('cancel')"
      />
    </div>

    <div v-if="loading" class="flex justify-center py-6">
      <UIcon name="i-lucide-loader-circle" class="size-6 animate-spin text-muted-foreground" />
    </div>

    <template v-else>
      <div class="overflow-x-auto rounded-md border border-default">
        <table class="w-full text-sm">
          <thead class="bg-muted/50 text-left">
            <tr>
              <th v-if="rows.length > 1" class="px-3 py-2 w-10" />
              <th class="px-3 py-2">{{ t('pages.report.columns.product') }}</th>
              <th class="px-3 py-2">{{ t('pages.report.columns.customer') }}</th>
              <th class="px-3 py-2 text-right">{{ t('pages.report.columns.amount') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="row in rows"
              :key="row.id ?? row.product"
              class="border-t border-default"
            >
              <td v-if="rows.length > 1" class="px-3 py-2">
                <UCheckbox
                  :model-value="isSelected(row.id, selectedIds)"
                  @update:model-value="emit('toggle-row', Number(row.id), !!$event)"
                />
              </td>
              <td class="px-3 py-2 font-medium">{{ row.product }}</td>
              <td class="px-3 py-2 text-muted-foreground">{{ row.customer }}</td>
              <td class="px-3 py-2 text-right font-medium text-primary">
                {{ formatCurrency(row.amount, 'USD') }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <UFormField :label="t('pages.report.refundDialog.reason')" required>
        <UTextarea
          v-model="refundReason"
          :placeholder="t('pages.report.refundDialog.reasonPlaceholder')"
          :rows="3"
          class="w-full"
        />
      </UFormField>

      <div class="flex justify-end gap-2">
        <UButton color="neutral" variant="ghost" :disabled="submitting" @click="emit('cancel')">
          {{ t('actions.cancel') }}
        </UButton>
        <UButton
          color="warning"
          variant="solid"
          icon="i-lucide-rotate-ccw"
          :loading="submitting"
          :disabled="!refundReason.trim() || submitting || !rows.length"
          @click="emit('confirm')"
        >
          {{ t('pages.report.refundDialog.confirm') }}
        </UButton>
      </div>
    </template>
  </div>
</template>
