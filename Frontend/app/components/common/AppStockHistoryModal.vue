<script setup lang="ts">
/**
 * Reusable Stock History Modal Component
 * Displays a table of stock additions or damages for a specific product.
 */
const open = defineModel<boolean>('open', { default: false })
const range = defineModel<any>('range')
const pagination = defineModel<any>('pagination', {
    default: () => ({ pageIndex: 0, pageSize: 50 })
})

const props = defineProps<{
    type: 'added' | 'damaged'
    productName?: string
    data: any[]
    loading?: boolean
    total: number
}>()

const { t } = useI18n()

const columns = [
    { accessorKey: 'id', header: t('product.id') },
    { accessorKey: 'qty', header: t('product.qty') },
    { accessorKey: 'note', header: t('product.note') },
    { accessorKey: 'createdAt', header: t('product.createdAt') }
]
</script>

<template>
    <UModal v-model:open="open" :dismissible="false" :ui="{ content: 'sm:max-w-4xl h-[80vh] flex flex-col' }">
        <template #header>
            <div class="flex items-center justify-between w-full">
                <div class="flex items-center gap-2">
                    <h3 class="font-semibold">{{ productName }}</h3>
                    <UBadge :color="type === 'added' ? 'primary' : 'error'" variant="soft" size="sm">
                        {{ type === 'added' ? $t('product.historyTitleAdded') : $t('product.historyTitleDamaged') }}
                    </UBadge>
                </div>
                <div class="flex items-center gap-2">
                    <CommonAppDatepicker v-model:range="range" />
                    <UButton
                        icon="i-lucide-x"
                        color="neutral"
                        variant="ghost"
                        size="sm"
                        @click="open = false"
                    />
                </div>
            </div>
        </template>

        <template #body>
            <TableApptable
                :columns="columns"
                :data="data"
                :loading="loading"
                :total-rows="total"
                v-model:pagination="pagination"
                :selectable="false"
                class="h-full"
            >
                <template #id-cell="{ row }">
                    <span class="text-xs text-muted-foreground">#{{ row.original.id }}</span>
                </template>
                <template #qty-cell="{ row }">
                    <UBadge :color="type === 'added' ? 'primary' : 'error'" variant="soft">
                        {{ type === 'added' ? '+' : '-' }}{{ row.original.qty }}
                    </UBadge>
                </template>
                <template #createdAt-cell="{ row }">
                    <span class="text-sm text-muted-foreground">
                        {{ formatDate(row.original.createdAt) }}
                    </span>
                </template>
            </TableApptable>
        </template>
    </UModal>
</template>
