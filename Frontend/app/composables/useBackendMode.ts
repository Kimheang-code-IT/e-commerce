export function useBackendMode() {
  const config = useRuntimeConfig()
  return computed(() => Boolean(config.public.useBackendApi))
}
