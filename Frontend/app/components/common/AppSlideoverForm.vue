<script setup lang="ts">
import { ref, watch, computed, onBeforeUnmount, nextTick } from 'vue'
import { parseDate } from '@internationalized/date'
import type { FormField } from '~/types'
import { sanitizeByTextRule, textRuleErrorMessage, resolveCurrencyPrefix } from '~/utils/validation/textRules'
const open = defineModel<boolean>('open')
type FormRecord = Record<string, any>

const props = defineProps<{
    data?: FormRecord
    title?: string
    submitLabel?: string
    fields?: FormField[]
}>()

const emit = defineEmits<{
    (e: 'submit', data: FormRecord): void
}>()

const { t } = useI18n()

// Internal form state
const formData = ref<FormRecord>({})
const filePreviewSources = ref<Record<string, string>>({})
const filePreviewObjectUrls = ref<Record<string, string>>({})
const lastSelectedFiles = ref<Record<string, File | null>>({})
const fileUploadRenderKeys = ref<Record<string, number>>({})
const showPasswords = ref<Record<string, boolean>>({})
const validationAttempted = ref(false)
const formBodyRef = ref<HTMLElement | null>(null)

function togglePassword(key: string) {
    showPasswords.value[key] = !showPasswords.value[key]
}

// Fields are now required to be passed as props for maximum flexibility across all pages
const activeFields = computed(() => props.fields || [])
function getCurrentImageKey(fieldKey: string) {
    return `${fieldKey}Current`
}

function resolveFirstFile(value: any): File | null {
    if (!value) return null
    if (value instanceof File) return value
    if (Array.isArray(value) && value.length > 0) {
        const first = value[0]
        if (first instanceof File) return first
        if (first?.file instanceof File) return first.file
    }
    if (value?.file instanceof File) return value.file
    return null
}

function normalizeFileUploadValue(value: any): File[] {
    const selectedFile = resolveFirstFile(value)
    return selectedFile ? [selectedFile] : []
}

function revokePreviewUrl(fieldKey: string) {
    const objectUrl = filePreviewObjectUrls.value[fieldKey]
    if (!objectUrl) return
    URL.revokeObjectURL(objectUrl)
    delete filePreviewObjectUrls.value[fieldKey]
}

function syncFilePreview(fieldKey: string) {
    const selectedFile = resolveFirstFile(formData.value[fieldKey])
    if (selectedFile) {
        if (lastSelectedFiles.value[fieldKey] !== selectedFile) {
            revokePreviewUrl(fieldKey)
            filePreviewObjectUrls.value[fieldKey] = URL.createObjectURL(selectedFile)
            lastSelectedFiles.value[fieldKey] = selectedFile
        }
        filePreviewSources.value[fieldKey] = String(filePreviewObjectUrls.value[fieldKey] ?? '')
        return
    }

    lastSelectedFiles.value[fieldKey] = null
    revokePreviewUrl(fieldKey)
    filePreviewSources.value[fieldKey] = String(formData.value[getCurrentImageKey(fieldKey)] || '')
}

function reloadImagePreview(fieldKey: string) {
    const src = String(filePreviewSources.value[fieldKey] || '')
    if (!src || src.startsWith('blob:')) return

    try {
        const url = new URL(src, window.location.origin)
        url.searchParams.set('_ts', String(Date.now()))
        filePreviewSources.value[fieldKey] = url.toString()
    } catch {
        const separator = src.includes('?') ? '&' : '?'
        filePreviewSources.value[fieldKey] = `${src}${separator}_ts=${Date.now()}`
    }
}

function resetFileUpload(fieldKey: string) {
    // Clear selected file and re-render upload input so same file can be selected again.
    formData.value[fieldKey] = []
    lastSelectedFiles.value[fieldKey] = null
    revokePreviewUrl(fieldKey)
    filePreviewSources.value[fieldKey] = String(formData.value[getCurrentImageKey(fieldKey)] || '')
    fileUploadRenderKeys.value[fieldKey] = (fileUploadRenderKeys.value[fieldKey] || 0) + 1
}

function clearImageSelection(fieldKey: string) {
    // Clear both new selection and existing image reference.
    formData.value[fieldKey] = []
    formData.value[getCurrentImageKey(fieldKey)] = ''
    lastSelectedFiles.value[fieldKey] = null
    revokePreviewUrl(fieldKey)
    filePreviewSources.value[fieldKey] = ''
    fileUploadRenderKeys.value[fieldKey] = (fileUploadRenderKeys.value[fieldKey] || 0) + 1
}

function selectDefaultForField(field: FormField) {
    const items = field.items
    if (!items || items.length === 0) return undefined
    const first = items[0] as Record<string, unknown> | string | number
    if (first && typeof first === 'object' && 'value' in first) {
        return first.value
    }
    return first as string | number | undefined
}

function initializeFormData(source?: FormRecord) {
    if (source) {
        const dataCopy: FormRecord = { ...source }
        activeFields.value.forEach(field => {
            if (field.type === 'date' && typeof dataCopy[field.key] === 'string' && dataCopy[field.key]) {
                try {
                    dataCopy[field.key] = parseDate(dataCopy[field.key])
                } catch {
                    dataCopy[field.key] = undefined
                }
            } else if (field.type === 'file') {
                dataCopy[getCurrentImageKey(field.key)] = dataCopy[field.key] || ''
                dataCopy[field.key] = []
                fileUploadRenderKeys.value[field.key] = (fileUploadRenderKeys.value[field.key] || 0) + 1
            } else if (field.type === 'money-tabs') {
                dataCopy[moneyTabsModeKey(field.key)] = 'usd'
                const usd = Math.max(0, Number(dataCopy[field.key] ?? 0))
                dataCopy[field.key] = usd
                dataCopy[moneyTabsInputKey(field.key)] = usd
            }
        })
        formData.value = dataCopy
        return
    }

    const initial: FormRecord = {}
    activeFields.value.forEach(field => {
        if (field.type === 'select' && field.items) {
            initial[field.key] = field.multiple ? [] : selectDefaultForField(field)
        } else if (field.type === 'permission-tree') {
            initial[field.key] = []
        } else if (field.type === 'date') {
            initial[field.key] = undefined
        } else if (field.type === 'file') {
            initial[field.key] = []
            initial[getCurrentImageKey(field.key)] = ''
            fileUploadRenderKeys.value[field.key] = (fileUploadRenderKeys.value[field.key] || 0) + 1
        } else if (field.type === 'money-tabs') {
            initial[field.key] = 0
            initial[moneyTabsModeKey(field.key)] = 'usd'
            initial[moneyTabsInputKey(field.key)] = 0
        } else {
            initial[field.key] = ''
        }
    })
    formData.value = initial
}

function normalizeNumberInput(value: unknown) {
    const raw = String(value ?? '')
    // Allow only non-negative numbers with one decimal point.
    let cleaned = raw.replace(/[^\d.]/g, '')
    const firstDot = cleaned.indexOf('.')
    if (firstDot !== -1) {
        cleaned = cleaned.slice(0, firstDot + 1) + cleaned.slice(firstDot + 1).replace(/\./g, '')
    }
    return cleaned
}

function isUsdField(field: FormField) {
    return field.type === 'currency' || field.currency === 'USD'
}

function moneyTabsModeKey(fieldKey: string) {
    return `${fieldKey}Mode`
}

function moneyTabsInputKey(fieldKey: string) {
    return `${fieldKey}Input`
}

function moneyTabsRefPrice(field: FormField): number {
    if (!field.refPriceKey) return 0
    return Math.max(0, Number(formData.value[field.refPriceKey] ?? 0))
}

function syncMoneyTabsField(field: FormField) {
    const mode = formData.value[moneyTabsModeKey(field.key)] === 'percent' ? 'percent' : 'usd'
    const input = Math.max(0, Number(formData.value[moneyTabsInputKey(field.key)] ?? 0))
    if (mode === 'percent') {
        const pct = Math.min(100, input)
        const base = moneyTabsRefPrice(field)
        formData.value[field.key] = Math.round(((base * pct) / 100) * 100) / 100
    } else {
        formData.value[field.key] = input
    }
}

function moneyTabsError(field: FormField): string {
    const mode = formData.value[moneyTabsModeKey(field.key)] === 'percent' ? 'percent' : 'usd'
    const input = Number(formData.value[moneyTabsInputKey(field.key)])
    if (!Number.isFinite(input)) return t('pages.pos.validation.numberRequired')
    const min = field.min ?? 0
    if (mode === 'percent') {
        if (input < 0) return t('pages.pos.validation.numberRequired')
        if (input > 100) return t('pages.pos.validation.discountPercentMax')
        return ''
    }
    if (input < min) return t('pages.pos.validation.minUsd', { min })
    const base = moneyTabsRefPrice(field)
    if (field.max != null && input > field.max) return t('pages.pos.validation.maxUsd', { max: field.max })
    if (base > 0 && input > base) return t('pages.pos.validation.discountUsdMax')
    return ''
}

function onMoneyTabsModeChange(field: FormField, mode: string) {
    const usd = Math.max(0, Number(formData.value[field.key] ?? 0))
    const base = moneyTabsRefPrice(field)
    if (mode === 'percent') {
        formData.value[moneyTabsInputKey(field.key)] =
            base > 0 ? Math.round((usd / base) * 10000) / 100 : 0
    } else {
        formData.value[moneyTabsInputKey(field.key)] = usd
    }
    syncMoneyTabsField(field)
}

function onNumberInput(fieldKey: string, event: Event) {
    const target = event.target as HTMLInputElement | null
    formData.value[fieldKey] = normalizeNumberInput(target?.value ?? '')
}

function usdFieldError(field: FormField): string {
    if (!isUsdField(field)) return ''
    const raw = formData.value[field.key]
    if (raw === '' || raw === undefined || raw === null) return ''
    const v = Number(raw)
    if (!Number.isFinite(v)) return t('pages.pos.validation.numberRequired')
    const min = field.min ?? 0
    if (v < min) return t('pages.pos.validation.minUsd', { min })
    if (field.max != null && v > field.max) return t('pages.pos.validation.maxUsd', { max: field.max })
    return ''
}

function numberFieldError(field: FormField): string {
    if (field.type !== 'number') return ''
    const raw = formData.value[field.key]
    if (raw === '' || raw === undefined || raw === null) return ''
    const v = Number(raw)
    if (!Number.isFinite(v)) return t('pages.pos.validation.numberRequired')
    const min = field.min ?? 0
    if (v < min) return t('pages.pos.validation.minUsd', { min })
    if (field.max != null && v > field.max) return t('pages.pos.validation.maxUsd', { max: field.max })
    return ''
}

function languageFieldError(field: FormField): string {
    if ((field.type !== 'input' && field.type !== 'textarea') || !field.textRule) return ''
    const raw = String(formData.value[field.key] ?? '')
    return textRuleErrorMessage(field, raw)
}

function requiredMessage(field: FormField, kind: 'default' | 'select' | 'multi' | 'file' = 'default') {
    const label = field.label || field.key
    if (kind === 'select') return t('components.validation.selectOption', { field: label })
    if (kind === 'multi') return t('components.validation.selectAtLeastOne', { field: label })
    if (kind === 'file') return t('components.validation.uploadImage', { field: label })
    return t('components.validation.required', { field: label })
}

function isFieldValueEmpty(field: FormField): boolean {
    const type = field.type || 'input'
    const value = formData.value[field.key]

    if (type === 'select' && field.multiple) {
        return !Array.isArray(value) || value.length === 0
    }
    if (type === 'select') {
        return value === undefined || value === null || value === ''
    }
    if (type === 'permission-tree') {
        return !Array.isArray(value) || value.length === 0
    }
    if (type === 'date') {
        return value === undefined || value === null
    }
    if (type === 'file') {
        const hasNew = normalizeFileUploadValue(value).length > 0
        const hasCurrent = String(formData.value[getCurrentImageKey(field.key)] || '').trim() !== ''
        return !hasNew && !hasCurrent
    }
    if (type === 'money-tabs') {
        const input = formData.value[moneyTabsInputKey(field.key)]
        if (input === '' || input === undefined || input === null) return true
        return !Number.isFinite(Number(input))
    }
    if (type === 'number' || type === 'currency' || field.currency === 'USD') {
        return String(value ?? '').trim() === ''
    }
    return String(value ?? '').trim() === ''
}

function validateField(field: FormField): string {
    if (field.required) {
        if (isFieldValueEmpty(field)) {
            const type = field.type || 'input'
            if (type === 'select' && field.multiple) return requiredMessage(field, 'multi')
            if (type === 'select') return requiredMessage(field, 'select')
            if (type === 'file') return requiredMessage(field, 'file')
            return requiredMessage(field)
        }
    }
    if (field.type === 'money-tabs') {
        const err = moneyTabsError(field)
        if (err) return err
    }
    if (isUsdField(field)) {
        const err = usdFieldError(field)
        if (err) return err
    }
    const numberErr = numberFieldError(field)
    if (numberErr) return numberErr
    const langErr = languageFieldError(field)
    if (langErr) return langErr
    return ''
}

function getFieldError(field: FormField): string {
    if (validationAttempted.value) return validateField(field)
    if (field.type === 'money-tabs') return moneyTabsError(field)
    if (isUsdField(field)) return usdFieldError(field)
    if (field.type === 'number') return numberFieldError(field)
    return languageFieldError(field)
}

function onTextInput(field: FormField, event: Event) {
    if (!field.textRule) return
    const target = event.target as HTMLInputElement | HTMLTextAreaElement | null
    if (!target) return
    const raw = target.value ?? ''
    const sanitized = sanitizeByTextRule(field.textRule, raw)
    if (sanitized !== raw) {
        target.value = sanitized
    }
    formData.value[field.key] = sanitized
}

function currencyPrefix(field: FormField): string {
    return resolveCurrencyPrefix(field)
}

function hasFieldError(field: FormField): boolean {
    return Boolean(getFieldError(field))
}

function resetValidation() {
    validationAttempted.value = false
}

function validateAll(): boolean {
    validationAttempted.value = true
    const firstInvalid = activeFields.value.find(field => validateField(field))
    if (!firstInvalid) return true
    nextTick(() => {
        const root = formBodyRef.value
        if (!root) return
        const el = root.querySelector('[data-field-error="true"]') as HTMLElement | null
        el?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    })
    return false
}

// Watch for data changes to sync form data
watch(() => props.data, (newVal) => {
    initializeFormData(newVal)
}, { immediate: true })

watch(open, (isOpen) => {
    if (!isOpen) {
        resetValidation()
        return
    }
    resetValidation()
    // Re-initialize every open so edit/new file upload always starts clean.
    initializeFormData(props.data)
})

watch([formData, activeFields], () => {
    activeFields.value
        .filter(field => field.type === 'file')
        .forEach(field => syncFilePreview(field.key))
    activeFields.value
        .filter(field => field.type === 'money-tabs')
        .forEach(field => syncMoneyTabsField(field))
}, { deep: true, immediate: true })

onBeforeUnmount(() => {
    Object.keys(filePreviewObjectUrls.value).forEach(revokePreviewUrl)
})

function onSave() {
    if (!validateAll()) return

    // Process form data back to plain objects (e.g. format dates back to string)
    const result = { ...formData.value }
    activeFields.value.forEach(field => {
        if (field.type === 'date' && result[field.key] && typeof result[field.key].toString === 'function') {
            result[field.key] = result[field.key].toString()
        } else if (field.type === 'money-tabs') {
            syncMoneyTabsField(field)
            result[field.key] = Number(result[field.key] ?? 0)
            delete result[moneyTabsModeKey(field.key)]
            delete result[moneyTabsInputKey(field.key)]
        } else if (field.type === 'number' || field.type === 'currency' || field.currency === 'USD') {
            const value = String(result[field.key] ?? '').trim()
            result[field.key] = value === '' ? 0 : Number(value)
        } else if (field.type === 'file') {
            // Emit file fields as normalized File[] and keep `<fieldKey>Current`
            // so parent logic can distinguish unchanged image vs new selection.
            result[field.key] = normalizeFileUploadValue(result[field.key])
            result[getCurrentImageKey(field.key)] = String(result[getCurrentImageKey(field.key)] || '')
        }
    })
    emit('submit', result)
}
</script>

<template>
    <USlideover v-model:open="open" :title="title || $t('components.processData')" :dismissible="false"
        class="max-w-md">
        <template #header>
            <div class="flex items-center justify-between w-full px-1">
                <h3 class="font-semibold text-highlighted">
                    {{ title || $t('components.processData') }}
                </h3>
                <UButton icon="i-lucide-x" color="neutral" variant="ghost" size="sm" @click="open = false" />
            </div>
        </template>

        <template #body>
            <div ref="formBodyRef" class="flex flex-col space-y-3 px-1 w-full overflow-hidden">
                <template v-for="field in activeFields" :key="field.key">
                    <UFormField class="w-full" :data-field-error="hasFieldError(field) ? 'true' : undefined"
                        :error="getFieldError(field) || undefined">
                        <template #label>
                            <div class="flex items-center gap-1.5">

                                <span class="font-medium text-highlighted">{{ field.label }}</span>
                                <span v-if="field.required" class="text-error font-bold leading-none -mt-1">*</span>
                            </div>
                        </template>

                        <!-- INPUT TYPE -->
                        <UInput v-if="!field.type || field.type === 'input' || field.type === 'password'"
                            v-model="formData[field.key]"
                            :type="field.type === 'password' ? (showPasswords[field.key] ? 'text' : 'password') : 'text'"
                            :placeholder="field.placeholder" :disabled="field.readonly"
                            :color="hasFieldError(field) ? 'error' : undefined" size="lg" class="w-full"
                            @input="onTextInput(field, $event)">
                            <template v-if="field.type === 'password'" #trailing>
                                <UButton color="neutral" variant="ghost"
                                    :icon="showPasswords[field.key] ? 'i-lucide-eye-off' : 'i-lucide-eye'"
                                    class="-mr-1.5" size="sm" @click="togglePassword(field.key)" />
                            </template>
                        </UInput>

                        <!-- MONEY TABS (% or USD) — toggle on left of input; saves USD in field.key -->
                        <CommonAppMoneyModeInput v-else-if="field.type === 'money-tabs'"
                            v-model:mode="formData[moneyTabsModeKey(field.key)]"
                            v-model:input-value="formData[moneyTabsInputKey(field.key)]"
                            :placeholder="field.placeholder" :disabled="field.readonly"
                            :max-usd="moneyTabsRefPrice(field) || field.max" :error-message="moneyTabsError(field)"
                            :usd-preview="Number(formData[field.key] ?? 0)" show-usd-preview size="lg"
                            @mode-change="(m: 'usd' | 'percent') => onMoneyTabsModeChange(field, m)"
                            @input="syncMoneyTabsField(field)" />

                        <!-- NUMBER / CURRENCY (USD) TYPE -->
                        <div v-else-if="field.type === 'number' || field.type === 'currency' || field.currency === 'USD'"
                            class="w-full space-y-1">
                            <UInput v-model="formData[field.key]" type="number" inputmode="decimal"
                                :step="isUsdField(field) ? 0.01 : 'any'" :min="field.min ?? 0" :max="field.max"
                                :placeholder="field.placeholder" :disabled="field.readonly"
                                :color="hasFieldError(field) ? 'error' : undefined" size="lg"
                                class="w-full tabular-nums" :ui="isUsdField(field) ? { leading: 'ps-2' } : undefined"
                                @input="onNumberInput(field.key, $event)">
                                <template v-if="isUsdField(field)" #leading>
                                    <span class="text-xs font-semibold text-muted-foreground select-none">{{
                                        currencyPrefix(field) }}</span>
                                </template>
                            </UInput>
                        </div>

                        <!-- SELECT TYPE -->
                        <CommonAppMutilSelect v-else-if="field.type === 'select' && field.multiple"
                            v-model="formData[field.key]" :items="field.items || []"
                            :placeholder="field.placeholder || $t('components.select')"
                            :class="['w-full', hasFieldError(field) ? 'ring-2 ring-error rounded-md' : '']" />

                        <USelect v-else-if="field.type === 'select'" v-model="formData[field.key]" :items="field.items"
                            :color="hasFieldError(field) ? 'error' : undefined" size="lg" class="w-full" />

                        <!-- PERMISSION TREE TYPE -->
                        <div v-else-if="field.type === 'permission-tree'"
                            :class="hasFieldError(field) ? 'rounded-lg ring-2 ring-error p-0.5' : ''">
                            <CommonAppPermissionTreeSelect v-model="formData[field.key]"
                                :pages="(field.items || []) as string[]" :actions="(field.childItems || []) as string[]"
                                :actions-by-page="field.actionsByPage || {}" />
                        </div>

                        <!-- TEXTAREA TYPE -->
                        <UTextarea v-else-if="field.type === 'textarea'" v-model="formData[field.key]"
                            :placeholder="field.placeholder" :color="hasFieldError(field) ? 'error' : undefined"
                            autoresize size="md" class="w-full" @input="onTextInput(field, $event)" />

                        <!-- DATE TYPE -->
                        <UPopover v-else-if="field.type === 'date'" class="w-full">
                            <UButton :color="hasFieldError(field) ? 'error' : 'neutral'" variant="soft" size="lg"
                                class="w-full justify-start font-normal"
                                :class="hasFieldError(field) ? '' : 'text-muted-foreground'"
                                :label="formData[field.key] ? formData[field.key].toString() : (field.placeholder || $t('components.selectDate'))" />
                            <template #content>
                                <UCalendar v-model="formData[field.key]" class="p-2" />
                            </template>
                        </UPopover>

                        <!-- FILE TYPE (IMAGE ONLY) -->
                        <div v-else-if="field.type === 'file'" class="w-full"
                            :class="hasFieldError(field) ? 'rounded-lg ring-2 ring-error' : ''">
                            <UFileUpload :key="`${field.key}-${fileUploadRenderKeys[field.key] || 0}`"
                                v-model="formData[field.key]" icon="i-lucide-image"
                                :label="field.placeholder || $t('components.imageUploadReplace')"
                                :description="$t('components.imageUploadHint')" accept="image/*" :multiple="false"
                                class="w-full relative **:data-[slot=base]:min-h-0 **:data-[slot=base]:py-3">
                                <template #default>
                                    <div v-if="filePreviewSources[field.key]"
                                        class="w-full relative rounded-lg overflow-hidden border border-default pointer-events-none">
                                        <img :src="filePreviewSources[field.key]" alt="Current image"
                                            class="block w-full max-h-50 max-w-full object-contain" />
                                        <div
                                            class="absolute inset-x-0 bottom-0 bg-black/25 flex items-end justify-center p-2">
                                            <span class="text-white text-xs font-medium">
                                                {{ $t('components.imageUploadReplace') }}
                                            </span>
                                        </div>
                                    </div>
                                    <UButton v-if="filePreviewSources[field.key]" icon="i-lucide-x" color="primary"
                                        variant="solid" size="xs"
                                        class="absolute top-2 right-2 z-10 pointer-events-auto"
                                        @click.stop.prevent="clearImageSelection(field.key)" />
                                </template>
                            </UFileUpload>
                        </div>
                    </UFormField>
                </template>
            </div>
        </template>

        <template #footer>
            <div class="flex items-center justify-end gap-3 w-full px-1">
                <UButton :label="$t('components.cancel')" color="neutral" variant="soft" @click="open = false" />
                <UButton :label="submitLabel || $t('components.saveChanges')" color="primary" variant="solid"
                    class="font-semibold shadow-sm px-6" @click="onSave" />
            </div>
        </template>
    </USlideover>
</template>
