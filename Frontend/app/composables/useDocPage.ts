import type { DocPage } from '~/types/content'

export function queryDocPage(path: string) {
  return queryCollection('docs').path(path).first() as Promise<DocPage | null>
}

export function queryDocSurround(path: string) {
  return queryCollectionItemSurroundings('docs', path, {
    fields: ['description']
  })
}
