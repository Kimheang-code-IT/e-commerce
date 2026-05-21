import en from '../../i18n/locales/en.json'
import km from '../../i18n/locales/km.json'

/** Same keys as `provinces` in `i18n/locales/*.json` and `name` in `data/kh.json`. */
export const CAMBODIA_PROVINCE_IDS = Object.keys(
  (en as { provinces: Record<string, string> }).provinces
) as readonly string[]

/** Short labels on map — keys must match GeoJSON / API canonical names. */
export const PROVINCE_SHORTCUTS: Record<string, string> = {
  'Banteay Meanchey': 'BMC',
  Battambang: 'BTB',
  'Kampong Cham': 'KPC',
  'Kampong Chhnang': 'KCH',
  'Kampong Speu': 'KPS',
  'Kampong Thom': 'KPT',
  Kampot: 'KMP',
  Kandal: 'KND',
  Kep: 'KEP',
  'Koh Kong': 'KKG',
  Kratie: 'KRT',
  'Mondul Kiri': 'MDK',
  'Oddar Meanchey': 'OMC',
  Pailin: 'PLN',
  'Phnom Penh': 'PP',
  'Preah Sihanouk': 'SHV',
  'Preah Vihear': 'PVH',
  'Prey Veng': 'PVG',
  Pursat: 'PUR',
  'Ratanak Kiri': 'RTK',
  Siemreap: 'SRP',
  'Stung Treng': 'STR',
  'Svay Rieng': 'SVR',
  Takeo: 'TKO',
  'Tboung Khmum': 'TBK'
}

export function normalizeProvinceKey(name: string): string {
  return String(name || '')
    .trim()
    .toLowerCase()
    .replace(/\s+/g, '')
}

function buildAliasToCanonical(): Map<string, string> {
  const enP = (en as { provinces: Record<string, string> }).provinces
  const kmP = (km as { provinces: Record<string, string> }).provinces
  const map = new Map<string, string>()
  for (const id of Object.keys(enP)) {
    const variants = [id, enP[id], kmP[id]].filter(Boolean) as string[]
    for (const v of variants) {
      map.set(normalizeProvinceKey(v), id)
    }
  }
  return map
}

let aliasMap: Map<string, string> | null = null

/**
 * Map stored `customer_address` (English key, Khmer label, or legacy translated value)
 * to the canonical province id used on the map and in i18n keys.
 */
export type ProvinceSelectItem = { label: string; value: string }

/** POS / customer address dropdown: Nothing + all Cambodia provinces (i18n labels). */
export function buildCambodiaProvinceSelectItems(
  translate: (key: string) => string
): ProvinceSelectItem[] {
  const provinces = CAMBODIA_PROVINCE_IDS.map((id) => ({
    label: translate(`provinces.${id}`),
    value: id
  })).sort((a, b) => a.label.localeCompare(b.label, undefined, { sensitivity: 'base' }))

  return [{ label: translate('common.nothing'), value: 'Nothing' }, ...provinces]
}

export function resolveProvinceAlias(raw: string): string {
  if (!aliasMap) aliasMap = buildAliasToCanonical()
  const trimmed = raw.trim()
  if (!trimmed) return ''
  const key = normalizeProvinceKey(trimmed)
  return aliasMap.get(key) ?? trimmed
}
