<script setup lang="ts">
import type { FormSubmitEvent, AuthFormField } from '@nuxt/ui'
import { AuthKeys } from '~/utils/constants/app'
import { localStore } from '~/utils/storage/local'
import { useAuthSession } from '~/utils/auth/session'
import { useAuthApi } from '~/utils/api'
import { authSchemas } from '~/utils/validation/rules'

definePageMeta({
  layout: 'auth'
})

const { t } = useI18n()
const router = useRouter()
const toast = useToast()
const authSession = useAuthSession()
const authApi = useAuthApi()
const useBackendApi = useBackendMode()

useSeoMeta({
  title: () => t('pages.auth.loginTitle'),
  description: () => t('pages.auth.loginDesc')
})

const fields: AuthFormField[] = [{
  name: 'email',
  type: 'email',
  size: 'lg',
  label: t('pages.auth.email'),
  placeholder: t('pages.auth.emailPlaceholder'),
  required: true
}, {
  name: 'password',
  label: t('pages.auth.password'),
  type: 'password',
  size: 'lg',
  placeholder: t('pages.auth.passwordPlaceholder'),
  required: true
}, {
  name: 'remember',
  label: t('pages.auth.remember'),
  type: 'checkbox'
}]

const schema = authSchemas.login

type Schema = {
  email: string
  password: string
  remember?: boolean
}

async function onSubmit(payload: FormSubmitEvent<Schema>) {
  const { email, password, remember } = payload.data

  if (useBackendApi.value) {
    try {
      const res = await authApi.login({ email, password })
      authSession.login(res.tokens, { ...res.user })
      await router.push('/')
      return
    } catch {
      toast.add({
        title: t('pages.auth.loginFailedTitle'),
        description: t('pages.auth.loginFailedDesc'),
        color: 'error'
      })
      return
    }
  }

  if (email === 'heang@gmail.com' && password === '123456') {
    // Handle remember me
    if (remember) {
      localStore.set(AuthKeys.REMEMBER_ENABLED, '1')
      localStore.set(AuthKeys.REMEMBER_EMAIL, email)
    } else {
      localStore.remove(AuthKeys.REMEMBER_ENABLED)
      localStore.remove(AuthKeys.REMEMBER_EMAIL)
    }

    // Login
    authSession.login({ accessToken: 'verifiable-pdme-session-token', refreshToken: '' }, {
      name: 'Moeng Kimheang',
      email,
      avatar: 'https://ui-avatars.com/api/?name=Moeng+Kimheang&background=008037&color=fff',
      role: 'admin',
      pageAccess: ['admin:*']
    })
    await router.push('/')
  } else {
    toast.add({
      title: t('pages.auth.loginFailedTitle'),
      description: t('pages.auth.loginFailedDesc'),
      color: 'error'
    })
  }
}
</script>

<template>
  <div class="flex flex-col items-center justify-center">

    <UAuthForm :schema="schema" :description="t('pages.auth.loginDesc')" icon="i-lucide-lock" :fields="fields"
      :submit="{ label: t('pages.auth.loginBtn'), class: 'w-full h-10! text-xl font-normal' }" @submit="onSubmit">
      <template #leading>
        <img src="/assets/images/logo.png" alt="Logo" class="h-20 w-auto mx-auto " />
      </template>

      <template #footer>
        <div class="text-center">
          <span class="font-black">© <span class="font-normal text-sm">{{ $t('pages.auth.departmentLine')
              }}</span></span>
        </div>
      </template>
    </UAuthForm>

  </div>
</template>
