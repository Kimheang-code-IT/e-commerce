/** Whether the backend has zero users and needs /setup. */
export async function fetchNeedsSetup(): Promise<boolean> {
  const config = useRuntimeConfig()
  if (!config.public.useBackendApi) return false
  try {
    const res = await $fetch<{ data?: { needsSetup?: boolean } }>('/auth/setup/status', {
      baseURL: config.public.apiBase || '/api/v1',
    })
    return Boolean(res?.data?.needsSetup)
  } catch {
    return false
  }
}
