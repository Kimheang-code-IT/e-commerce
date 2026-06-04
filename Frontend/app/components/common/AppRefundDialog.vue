<script setup lang="ts">
import { watch } from 'vue'
import { formatCurrency } from '~/utils/format/currency'
import type { ReportRow } from '~/types'
import { sanitizeByTextRule } from '~/utils/validation/textRules'
import { modalUiConfirm, dialogFooterActions, dialogHeaderRow } from '~/utils/ui/overlayUi'

const open = defineModel<boolean>('open', { default: false })
const refundReason = defineModel<string>('reason', { default: '' })

defineProps<{
  row: ReportRow | null
  submitting?: boolean
}>()

const emit = defineEmits<{
  (e: 'confirm'): void
}>()

const { t } = useI18n()

watch(refundReason, (value) => {
  const sanitized = sanitizeByTextRule('text', String(value || ''))
  if (sanitized !== value) refundReason.value = sanitized
})
</script>

<template>
  <UModal v-model:open="open" :dismissible="false" :ui="modalUiConfirm">
    <template #header>
      <div :class="dialogHeaderRow">
        <h3 class="flex-1 min-w-0 text-sm font-semibold truncate">
          {{ t('pages.report.refundDialog.title') }}
        </h3>
        <UButton
          icon="i-lucide-x"
          color="neutral"
          variant="ghost"
          size="sm"
          square
          @click="open = false"
        />
      </div>
    </template>

    <template #body>
      <div v-if="row" class="space-y-4">
        <div class="text-sm space-y-1.5 rounded-md border border-default p-3 bg-muted/30">
          <p>
            <span class="text-muted-foreground">{{ t('pages.report.columns.invoiceNo') }}:</span>
            <strong class="ml-1">{{ row.invoiceNo }}</strong>
          </p>
          <p>
            <span class="text-muted-foreground">{{ t('pages.report.columns.product') }}:</span>
            <strong class="ml-1">{{ row.product }}</strong>
          </p>
          <p>
            <span class="text-muted-foreground">{{ t('pages.report.columns.amount') }}:</span>
            <strong class="ml-1 text-primary">{{ formatCurrency(row.amount, 'USD') }}</strong>
          </p>
        </div>

        <UFormField :label="t('pages.report.refundDialog.reason')" required>
          <UTextarea
            v-model="refundReason"
            :placeholder="t('pages.report.refundDialog.reasonPlaceholder')"
            :rows="3"
            class="w-full"
          />
        </UFormField>
      </div>
    </template>

    <template #footer>
      <div :class="dialogFooterActions">
        <UButton color="neutral" variant="ghost" @click="open = false">
          {{ t('actions.cancel') }}
        </UButton>
        <UButton
          type="button"
          color="warning"
          variant="solid"
          icon="i-lucide-rotate-ccw"
          :loading="submitting"
          :disabled="!refundReason.trim() || submitting"
          @click.stop="emit('confirm')"
        >
          {{ t('pages.report.refundDialog.confirm') }}
        </UButton>
      </div>
    </template>
  </UModal>
</template>
