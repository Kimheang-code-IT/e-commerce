/** Shared UModal / overlay layout classes for mobile-friendly centered dialogs. */

export const dialogContentSm =
  'w-[min(96vw,28rem)] max-w-[96vw] sm:max-w-md max-h-[min(88dvh,640px)] flex flex-col m-2 sm:m-0'

export const dialogContentTable =
  'w-[min(96vw,64rem)] max-w-[96vw] sm:max-w-5xl max-h-[min(88dvh,720px)] h-auto sm:h-[80vh] flex flex-col m-2 sm:m-0'

export const dialogBody = 'flex-1 min-h-0 overflow-auto px-3 py-2 sm:px-4 sm:py-3'

export const dialogHeader =
  'shrink-0 px-3 py-2 sm:px-4 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between w-full'

export const dialogFooter =
  'shrink-0 px-3 py-3 sm:px-4 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end overlay-safe-footer w-full'

export const dialogFooterActions = 'flex flex-col-reverse gap-2 sm:flex-row sm:justify-end w-full [&_button]:min-h-11'

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
