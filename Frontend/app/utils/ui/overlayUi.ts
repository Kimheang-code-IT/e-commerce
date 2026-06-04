/** Shared UModal / overlay layout classes. */

const mobileFullscreen =
  'max-sm:w-[100dvw] max-sm:max-w-[100dvw] max-sm:h-[100dvh] max-sm:max-h-[100dvh] max-sm:min-h-[100dvh] max-sm:m-0 max-sm:rounded-none'

/** Centered confirm / small dialogs (all breakpoints). */
export const dialogContentConfirm =
  'w-[min(96vw,28rem)] max-w-[96vw] sm:max-w-md max-h-[min(88dvh,640px)] flex flex-col m-2 sm:m-0'

/** Full-screen forms on mobile; slideover width on desktop. */
export const dialogContentForm = [
  'flex flex-col',
  mobileFullscreen,
  'w-[min(96vw,28rem)] max-w-[96vw] sm:max-w-md',
  'max-h-[min(88dvh,640px)] sm:max-h-[min(88dvh,640px)]',
  'sm:m-0',
].join(' ')

/** Table data dialogs — full screen on mobile. */
export const dialogContentTable = [
  'flex flex-col',
  mobileFullscreen,
  'w-[min(96vw,64rem)] max-w-[96vw] sm:max-w-5xl',
  'h-auto max-sm:h-[100dvh] sm:h-[80vh]',
  'max-h-[min(88dvh,720px)] sm:max-h-[min(88dvh,720px)]',
  'sm:m-0',
].join(' ')

export const dialogBody = 'flex-1 min-h-0 overflow-auto px-2 py-2 sm:px-4 sm:py-3'

export const dialogHeaderRow =
  'shrink-0 px-2 py-2 flex flex-nowrap items-center gap-2 w-full min-w-0'

export const dialogHeaderMeta = 'px-2 pb-2 flex flex-wrap items-center gap-1.5 w-full'

export const dialogFooter =
  'shrink-0 px-2 py-2 sm:py-3 flex flex-row flex-wrap justify-end items-center gap-2 overlay-safe-footer w-full'

/** Footer buttons always on one row (mobile + desktop). */
export const dialogFooterActions =
  'flex flex-row flex-wrap justify-end items-center gap-2 w-full [&_button]:min-h-10 sm:[&_button]:min-h-11'

export const modalUiConfirm = {
  content: dialogContentConfirm,
  header: 'border-none p-0 shrink-0',
  body: 'p-0 flex-1 min-h-0 overflow-hidden flex flex-col',
  footer: 'border-none p-0 shrink-0',
} as const

export const modalUiForm = {
  content: dialogContentForm,
  header: 'border-none p-0 shrink-0',
  body: 'p-0 flex-1 min-h-0 overflow-hidden flex flex-col',
  footer: 'border-none p-0 shrink-0',
} as const

export const modalUiTable = {
  content: dialogContentTable,
  header: 'border-none p-0 shrink-0',
  body: 'p-0 flex-1 min-h-0 overflow-hidden flex flex-col',
  footer: 'border-none p-0 shrink-0',
} as const

/** @deprecated Use modalUiConfirm or modalUiForm */
export const modalUiSm = modalUiConfirm
