<script setup lang="ts">
import { ref, watch, computed, onBeforeUnmount } from 'vue'
import { parseDate } from '@internationalized/date'
import type { FormField } from '~/types'
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

// Internal form state
const formData = ref<FormRecord>({})
const filePreviewSources = ref<Record<string, string>>({})
const filePreviewObjectUrls = ref<Record<string, string>>({})
const lastSelectedFiles = ref<Record<string, File | null>>({})
const fileUploadRenderKeys = ref<Record<string, number>>({})
const showPasswords = ref<Record<string, boolean>>({})

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
        } else {
            initial[field.key] = ''
        }
    })
    formData.value = initial
}

function normalizeNumberInput(value: unknown) {
    const raw = String(value ?? '')
    // Allow only digits, optional leading minus, and one decimal point.
    let cleaned = raw.replace(/[^\d.-]/g, '')
    cleaned = cleaned.replace(/(?!^)-/g, '')
    const firstDot = cleaned.indexOf('.')
    if (firstDot !== -1) {
        cleaned = cleaned.slice(0, firstDot + 1) + cleaned.slice(firstDot + 1).replace(/\./g, '')
    }
    return cleaned
}

function onNumberInput(fieldKey: string, event: Event) {
    const target = event.target as HTMLInputElement | null
    formData.value[fieldKey] = normalizeNumberInput(target?.value ?? '')
}

// Watch for data changes to sync form data
watch(() => props.data, (newVal) => {
    initializeFormData(newVal)
}, { immediate: true })

watch(open, (isOpen) => {
    if (!isOpen) return
    // Re-initialize every open so edit/new file upload always starts clean.
    initializeFormData(props.data)
})

watch([formData, activeFields], () => {
    activeFields.value
        .filter(field => field.type === 'file')
        .forEach(field => syncFilePreview(field.key))
}, { deep: true, immediate: true })

onBeforeUnmount(() => {
    Object.keys(filePreviewObjectUrls.value).forEach(revokePreviewUrl)
})

function onSave() {
    // Process form data back to plain objects (e.g. format dates back to string)
    const result = { ...formData.value }
    activeFields.value.forEach(field => {
        if (field.type === 'date' && result[field.key] && typeof result[field.key].toString === 'function') {
            result[field.key] = result[field.key].toString()
        } else if (field.type === 'number') {
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
  <USlideover 
    v-model:open="open" 
    :title="title || $t('components.processData')"
    :dismissible="false"
    class="max-w-md"
  >
    <template #header>
      <div class="flex items-center justify-between w-full px-1">
        <h3 class="font-semibold text-highlighted">
          {{ title || $t('components.processData') }}
        </h3>
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
      <div class="flex flex-col space-y-3 px-1 w-full overflow-hidden">
        <template v-for="field in activeFields" :key="field.key">
            <UFormField 
                class="w-full"
            >
                <template #label>
                    <div class="flex items-center gap-1.5">
 
                        <span class="font-medium text-highlighted">{{ field.label }}</span>
                        <span v-if="field.required" class="text-error font-bold leading-none -mt-1">*</span>
                    </div>
                </template>

                <!-- INPUT TYPE -->
                <UInput 
                    v-if="!field.type || field.type === 'input' || field.type === 'password'"
                    v-model="formData[field.key]"
                    :type="field.type === 'password' ? (showPasswords[field.key] ? 'text' : 'password') : 'text'"
                    :placeholder="field.placeholder" 
                    :disabled="field.readonly"
                    size="lg" 
                    class="w-full" 
                >
                    <template v-if="field.type === 'password'" #trailing>
                        <UButton
                            color="neutral"
                            variant="ghost"
                            :icon="showPasswords[field.key] ? 'i-lucide-eye-off' : 'i-lucide-eye'"
                            class="-mr-1.5"
                            size="sm"
                            @click="togglePassword(field.key)"
                        />
                    </template>
                </UInput>

                <!-- NUMBER TYPE -->
                <UInput
                    v-else-if="field.type === 'number'"
                    v-model="formData[field.key]"
                    type="number"
                    inputmode="decimal"
                    step="any"
                    :placeholder="field.placeholder"
                    :disabled="field.readonly"
                    size="lg"
                    class="w-full"
                    @input="onNumberInput(field.key, $event)"
                />

                <!-- SELECT TYPE -->
                <CommonAppMutilSelect
                    v-else-if="field.type === 'select' && field.multiple"
                    v-model="formData[field.key]"
                    :items="field.items || []"
                    :placeholder="field.placeholder || $t('components.select')"
                    class="w-full"
                />

                <USelect 
                    v-else-if="field.type === 'select'"
                    v-model="formData[field.key]"
                    :items="field.items"
                    size="lg" 
                    class="w-full" 
                />

                <!-- PERMISSION TREE TYPE -->
                <CommonAppPermissionTreeSelect
                    v-else-if="field.type === 'permission-tree'"
                    v-model="formData[field.key]"
                    :pages="(field.items || []) as string[]"
                    :actions="(field.childItems || []) as string[]"
                />

                <!-- TEXTAREA TYPE -->
                <UTextarea 
                    v-else-if="field.type === 'textarea'"
                    v-model="formData[field.key]"
                    :placeholder="field.placeholder"
                    autoresize 
                    size="md"
                    class="w-full"
                />

                <!-- DATE TYPE -->
                <UPopover v-else-if="field.type === 'date'" class="w-full">
                    <UButton 
                        color="neutral" variant="soft" 
                        size="lg" class="w-full justify-start font-normal text-muted-foreground"
                        :label="formData[field.key] ? formData[field.key].toString() : (field.placeholder || $t('components.selectDate'))"
                    />
                    <template #content>
                        <UCalendar v-model="formData[field.key]" class="p-2" />
                    </template>
                </UPopover>

                <!-- FILE TYPE (IMAGE ONLY) -->
                <div v-else-if="field.type === 'file'" class="w-full">
                    <UFileUpload
                        :key="`${field.key}-${fileUploadRenderKeys[field.key] || 0}`"
                        v-model="formData[field.key]"
                        icon="i-lucide-image"
                        :label="field.placeholder || 'Drop your image here'"
                        description="SVG, PNG, JPG or GIF (max. 2MB)"
                        accept="image/*"
                        :multiple="false"
                        class="w-full min-h-48 relative"
                    >
                        <template #default>
                            <div
                                v-if="filePreviewSources[field.key]"
                                class="w-full h-full min-h-48 relative rounded-lg overflow-hidden border border-default pointer-events-none"
                            >
                                <img
                                    :src="filePreviewSources[field.key]"
                                    alt="Current image"
                                    class="w-full h-full min-h-48 object-cover"
                                />
                                <div class="absolute inset-0 bg-black/25 flex items-end justify-center p-2">
                                    <span class="text-white text-xs font-medium">
                                        Click or drop to replace image
                                    </span>
                                </div>
                            </div>
                            <UButton
                                v-if="filePreviewSources[field.key]"
                                icon="i-lucide-x"
                                color="primary"
                                variant="solid"
                                size="xs"
                                class="absolute top-2 right-2 z-10 pointer-events-auto"
                                @click.stop.prevent="clearImageSelection(field.key)"
                            />
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
        <UButton 
            :label="submitLabel || $t('components.saveChanges')" 
            color="primary" 
            variant="solid" 
            class="font-semibold shadow-sm px-6"
            @click="onSave" 
        />
      </div>
    </template>
  </USlideover>
</template>
