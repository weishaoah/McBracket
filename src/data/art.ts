/**
 * Original flat illustrations, drawn as inline SVG.
 *
 * Official product photos are not reproduced here: they are not ours to
 * redistribute, and this project is not an official McDonald's product. Each
 * contender gets a hand-built glyph instead, keyed by product code. Anything
 * without an entry falls back to a neutral plate.
 */

export type ArtKind = 'beef' | 'double' | 'angus' | 'chicken' | 'fish' | 'wing' | 'cup' | 'apple' | 'generic'

export const ART_BY_CODE: Record<string, ArtKind> = {
  '1100': 'beef', // 巨无霸
  '511781': 'angus', // 培根安格斯厚牛堡
  '4648': 'double', // 不素之霸双层牛堡
  '1600': 'fish', // 麦香鱼
  '1450': 'chicken', // 麦香鸡
  '520445': 'wing', // 薄皮焦香V翅
  '2430': 'cup', // 【美汁源】黄金橙橙
  '6102': 'apple', // 苹果片
}

export const ART_PALETTE: Record<ArtKind, { bun: string; patty: string; accent: string }> = {
  beef: { bun: '#E8A33D', patty: '#8B4A2B', accent: '#7FBF5A' },
  double: { bun: '#E8A33D', patty: '#7A3F24', accent: '#F2C230' },
  angus: { bun: '#D98E33', patty: '#6E3820', accent: '#E2574C' },
  chicken: { bun: '#EDB04A', patty: '#D9963C', accent: '#8FCB62' },
  fish: { bun: '#EDB04A', patty: '#F3D9A4', accent: '#6FB7D8' },
  wing: { bun: '#D98E33', patty: '#C4742C', accent: '#F2C230' },
  cup: { bun: '#E2574C', patty: '#F2A03D', accent: '#FFD966' },
  apple: { bun: '#F2C230', patty: '#E8E1C8', accent: '#7FBF5A' },
  generic: { bun: '#D9A15B', patty: '#9A6B4F', accent: '#8B8B8B' },
}

export function artKind(code: string): ArtKind {
  return ART_BY_CODE[code] ?? 'generic'
}
