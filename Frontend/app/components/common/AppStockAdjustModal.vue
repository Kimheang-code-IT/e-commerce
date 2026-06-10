<script setup lang="ts">
const open = defineModel<boolean>("open", { default: false });
const qty = defineModel<number>("qty", { default: 0 });
const inPrice = defineModel<number>("inPrice", { default: 0 });
const outPrice = defineModel<number>("outPrice", { default: 0 });
const note = defineModel<string>("note", { default: "" });
const stockLotId = defineModel<number | null>("stockLotId", { default: null });

const props = withDefaults(
  defineProps<{
    mode?: "added" | "damaged";
    productName?: string;
    defaultInPrice?: number;
    defaultOutPrice?: number;
    stockLotOptions?: { label: string; value: number; qtyRemaining: number }[];
    stockLotsLoading?: boolean;
  }>(),
  {
    mode: "added",
    productName: "",
    defaultInPrice: 0,
    defaultOutPrice: 0,
    stockLotOptions: () => [],
    stockLotsLoading: false,
  },
);

const emit = defineEmits<{
  (e: "apply"): void;
}>();

const { t } = useI18n();

const stockLotIdForSelect = computed({
  get: () => stockLotId.value ?? undefined,
  set: (value: number | undefined) => {
    stockLotId.value = value ?? null;
  },
});

const selectedLotRemaining = computed(() => {
  if (!stockLotId.value) return null;
  const opt = props.stockLotOptions.find((o) => o.value === stockLotId.value);
  return opt ? opt.qtyRemaining : null;
});

const canApply = computed(() => {
  const q = Number(qty.value);
  if (!Number.isFinite(q) || q <= 0) return false;
  if (props.mode === "added") {
    const cost = Number(inPrice.value);
    const sale = Number(outPrice.value);
    return Number.isFinite(cost) && cost >= 0 && Number.isFinite(sale) && sale >= 0;
  }
  if (props.stockLotsLoading) return false;
  if (!props.stockLotOptions.length) return false;
  if (!stockLotId.value) return false;
  const left = selectedLotRemaining.value;
  if (left != null && q > left) return false;
  return true;
});
</script>

<template>
  <UModal v-model:open="open" :dismissible="false" :ui="{ content: 'max-w-md' }">
    <template #header>
      <div class="flex items-center justify-between w-full">
        <div class="flex items-center gap-2">
          <h3 class="font-semibold">{{ productName }}</h3>
          <UBadge :color="mode === 'added' ? 'primary' : 'error'" variant="soft" size="sm">
            {{ mode === "added" ? $t("components.stockAdjust.titleAdd") : $t("components.stockAdjust.titleDamaged") }}
          </UBadge>
        </div>
        <UButton
          icon="i-lucide-x"
          color="neutral"
          variant="ghost"
          size="sm"
          @click="open = false"
        />
      </div>
    </template>

    <template #body>
      <div class="space-y-3">
        <template v-if="mode === 'damaged'">
          <p class="text-xs text-muted-foreground">
            {{ $t("components.stockAdjust.damagedLotHint") }}
          </p>
          <UFormField :label="$t('components.stockAdjust.selectStockLot')" required>
            <USelect
              v-model="stockLotIdForSelect"
              :items="stockLotOptions"
              value-key="value"
              label-key="label"
              :loading="stockLotsLoading"
              :disabled="!stockLotOptions.length && !stockLotsLoading"
              class="w-full"
              :placeholder="$t('components.stockAdjust.selectStockLotPlaceholder')"
            />
          </UFormField>
          <p
            v-if="!stockLotsLoading && !stockLotOptions.length"
            class="text-xs text-error"
          >
            {{ $t("components.stockAdjust.noOpenLots") }}
          </p>
        </template>

        <UFormField :label="mode === 'added' ? $t('components.stockAdjust.qtyToAdd') : $t('components.stockAdjust.qtyDamaged')">
          <UInput
            v-model.number="qty"
            type="number"
            min="1"
            :max="mode === 'damaged' && selectedLotRemaining != null ? selectedLotRemaining : undefined"
            step="1"
            placeholder="0"
            class="w-full"
          />
        </UFormField>

        <template v-if="mode === 'added'">
          <p class="text-xs text-muted-foreground">
            {{ $t("components.stockAdjust.fifoHint") }}
          </p>
          <UFormField :label="$t('product.inPrice')">
            <UInput
              v-model.number="inPrice"
              type="number"
              min="0"
              step="0.01"
              class="w-full"
              :ui="{ leading: 'ps-2' }"
            >
              <template #leading>
                <span class="text-xs font-semibold text-muted-foreground select-none">USD</span>
              </template>
            </UInput>
          </UFormField>

          <UFormField :label="$t('product.outPrice')">
            <UInput
              v-model.number="outPrice"
              type="number"
              min="0"
              step="0.01"
              class="w-full"
              :ui="{ leading: 'ps-2' }"
            >
              <template #leading>
                <span class="text-xs font-semibold text-muted-foreground select-none">USD</span>
              </template>
            </UInput>
          </UFormField>
        </template>

        <UFormField :label="$t('product.note')">
          <UTextarea
            v-model="note"
            :placeholder="$t('product.note')"
            class="w-full"
            :rows="3"
          />
        </UFormField>
      </div>
    </template>

    <template #footer>
      <div class="flex justify-end gap-2 w-full">
        <UButton color="neutral" variant="soft" @click="open = false">
          {{ $t("actions.cancel") }}
        </UButton>
        <UButton
          :color="mode === 'added' ? 'primary' : 'warning'"
          :disabled="!canApply"
          @click="emit('apply')"
        >
          {{ $t("actions.confirm") }}
        </UButton>
      </div>
    </template>
  </UModal>
</template>
