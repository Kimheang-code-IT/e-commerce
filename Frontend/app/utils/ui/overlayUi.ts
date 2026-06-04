/** Shared UModal / overlay layout classes for mobile-friendly overlays. */

const mobileFullscreen =
  'max-sm:w-[100dvw] max-sm:max-w-[100dvw] max-sm:h-[100dvh] max-sm:max-h-[100dvh] max-sm:min-h-[100dvh] max-sm:m-0 max-sm:rounded-none'

export const dialogContentSm = [
  'flex flex-col',
  mobileFullscreen,
  'w-[min(96vw,28rem)] max-w-[96vw] sm:max-w-md',
  'max-h-[min(88dvh,640px)] sm:max-h-[min(88dvh,640px)]',
  'sm:m-0',
].join(' ')

export const dialogContentTable = [
  'flex flex-col',
  mobileFullscreen,
  'w-[min(96vw,64rem)] max-w-[96vw] sm:max-w-5xl',
  'h-auto max-sm:h-[100dvh] sm:h-[80vh]',
  'max-h-[min(88dvh,720px)] sm:max-h-[min(88dvh,720px)]',
  'sm:m-0',
].join(' ')

export const dialogBody = 'flex-1 min-h-0 overflow-auto px-3 py-2 sm:px-4 sm:py-3 max-sm:px-2 max-sm:py-2'

export const dialogHeader =
  'shrink-0 px-3 py-2 sm:px-4 max-sm:px-2 max-sm:py-2 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between w-full'

export const dialogFooter =
  'shrink-0 px-3 py-3 sm:px-4 max-sm:px-2 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end overlay-safe-footer w-full'

export const dialogFooterActions =
  'flex flex-col-reverse gap-2 sm:flex-row sm:justify-end w-full [&_button]:min-h-11'

export const modalUiSm = {
  content: dialogContentSm,
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
