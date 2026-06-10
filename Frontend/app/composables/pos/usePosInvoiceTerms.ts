export function usePosInvoiceTerms() {
  const { t } = useI18n()

  const termsTitle = computed(() => t('pages.pos.invoice.terms.title'))
  const termsLines = computed(() => [
    { km: t('pages.pos.invoice.terms.km'), en: t('pages.pos.invoice.terms.en') },
  ])

  return { termsTitle, termsLines }
}
