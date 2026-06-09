<script setup lang="ts">
import type { FormSubmitEvent, AuthFormField } from '@nuxt/ui'
import { useAuthApi } from '~/utils/api'
import { fetchNeedsSetup } from '~/utils/auth/setup'
import { authSchemas } from '~/utils/validation/rules'

definePageMeta({
  layout: 'auth'
})

const { t } = useI18n()
const router = useRouter()
const toast = useToast()
const authApi = useAuthApi()
const useBackendApi = useBackendMode()

useSeoMeta({
  title: () => t('pages.auth.setupTitle'),
  description: () => t('pages.auth.setupDesc')
})

const fields = computed<AuthFormField[]>(() => [
  {
    name: 'name',
    type: 'text',
    size: 'lg',
    label: t('pages.auth.setupName'),
    placeholder: t('pages.auth.setupNamePlaceholder'),
    required: true
  },
  {
    name: 'email',
    type: 'email',
    size: 'lg',
    label: t('pages.auth.email'),
    placeholder: t('pages.auth.emailPlaceholder'),
    required: true
  },
  {
    name: 'password',
    label: t('pages.auth.password'),
    type: 'password',
    size: 'lg',
    placeholder: t('pages.auth.setupPasswordPlaceholder'),
    required: true
  },
  {
    name: 'passwordConfirm',
    label: t('pages.auth.setupPasswordConfirm'),
    type: 'password',
    size: 'lg',
    placeholder: t('pages.auth.setupPasswordConfirmPlaceholder'),
    required: true
  }
])

const schema = authSchemas.setup

type Schema = {
  name: string
  email: string
  password: string
  passwordConfirm: string
}

const checkingStatus = ref(true)

async function ensureSetupAllowed() {
  if (!useBackendApi.value) {
    await router.replace('/login')
    checkingStatus.value = false
    return
  }
  const needsSetup = await fetchNeedsSetup()
  if (!needsSetup) {
    await router.replace('/login')
  }
  checkingStatus.value = false
}

onMounted(() => {
  ensureSetupAllowed()
})

async function onSubmit(payload: FormSubmitEvent<Schema>) {
  const { name, email, password, passwordConfirm } = payload.data

  if (!useBackendApi.value) {
    toast.add({
      title: t('common.error'),
      description: t('pages.auth.setupBackendRequired'),
      color: 'error'
    })
    return
  }

  try {
    const res = await authApi.setupBootstrap({ name, email, password, passwordConfirm })
    toast.add({
      title: t('pages.auth.setupSuccessTitle'),
      description: res.message || t('pages.auth.setupSuccessDesc'),
      color: 'primary'
    })
    await router.push('/login')
  } catch (err: unknown) {
    const message =
      (err as { response?: { _data?: { message?: string } } })?.response?._data?.message ||
      t('pages.auth.setupFailedDesc')
    toast.add({
      title: t('pages.auth.setupFailedTitle'),
      description: message,
      color: 'error'
    })
  }
}
</script>

<template>
  <div class="flex flex-col items-center justify-center">
    <div v-if="checkingStatus" class="flex flex-col items-center gap-3 py-8 text-muted-foreground">
      <UIcon name="i-lucide-loader-circle" class="size-8 animate-spin" />
      <span class="text-sm">{{ $t('pages.auth.setupChecking') }}</span>
    </div>

    <UAuthForm
      v-else
      :schema="schema"
      :title="t('pages.auth.setupTitle')"
      icon="i-lucide-shield-plus"
      :fields="fields"
      :submit="{ label: t('pages.auth.setupBtn'), class: 'w-full h-10! text-base font-normal' }"
      @submit="onSubmit"
    >
      <template #leading>
        <img src="/assets/images/logo.png" alt="Anya Music School" class="h-20 w-auto mx-auto" />
      </template>

      <template #footer>
        <div class="text-center space-y-2">
          <div>
            <span class="font-black"
              >© <span class="font-normal text-sm">{{ $t('pages.auth.departmentLine') }}</span></span
            >
          </div>
        </div>
      </template>
    </UAuthForm>
  </div>
</template>
