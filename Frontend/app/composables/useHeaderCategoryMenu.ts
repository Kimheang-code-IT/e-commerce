const isOpen = ref(false)
const triggerRef = ref<HTMLElement | null>(null)

export function useHeaderCategoryMenu() {
  const open = () => {
    isOpen.value = true
  }

  const close = () => {
    isOpen.value = false
  }

  const toggle = () => {
    isOpen.value = !isOpen.value
  }

  return {
    isOpen,
    triggerRef,
    open,
    close,
    toggle
  }
}
