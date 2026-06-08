export interface AuthUser {
  name: string
  email?: string
  phone?: string
}

function deriveName(phone?: string, email?: string, name?: string) {
  if (name) {
    return name
  }

  if (email) {
    return email.split('@')[0] || 'User'
  }

  if (phone) {
    const digits = phone.replace(/\D/g, '')
    return digits ? `User ${digits.slice(-4)}` : 'User'
  }

  return 'User'
}

export function useAuth() {
  const user = useCookie<AuthUser | null>('auth-user', {
    default: () => null,
    maxAge: 60 * 60 * 24 * 30
  })

  const isLoggedIn = computed(() => !!user.value)

  function login(credentials: { phone?: string; email?: string; name?: string }) {
    user.value = {
      name: deriveName(credentials.phone, credentials.email, credentials.name),
      phone: credentials.phone,
      email: credentials.email
    }
  }

  function logout() {
    const localePath = useLocalePath()
    user.value = null
    navigateTo(localePath('/login'))
  }

  return {
    user,
    isLoggedIn,
    login,
    logout
  }
}
