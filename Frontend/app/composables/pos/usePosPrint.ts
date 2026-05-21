import { ref } from 'vue'

export function usePosPrint() {
  const isCheckoutConfirmOpen = ref(false)
  const isFinishDialogOpen = ref(false)

  function openCheckoutConfirm() {
    isCheckoutConfirmOpen.value = true
  }

  function closeCheckoutConfirm() {
    isCheckoutConfirmOpen.value = false
  }

  function openPrintDialog() {
    isFinishDialogOpen.value = true
  }

  function closePrintDialog() {
    isFinishDialogOpen.value = false
  }

  function confirmCheckoutAndContinue() {
    closeCheckoutConfirm()
    openPrintDialog()
  }

  return {
    isCheckoutConfirmOpen,
    isFinishDialogOpen,
    openCheckoutConfirm,
    closeCheckoutConfirm,
    confirmCheckoutAndContinue,
    openPrintDialog,
    closePrintDialog
  }
}