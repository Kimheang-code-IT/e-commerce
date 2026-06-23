import { copyFile, mkdir } from 'node:fs/promises'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import sharp from 'sharp'

const rootDir = join(dirname(fileURLToPath(import.meta.url)), '..')
const imageDir = join(rootDir, 'public/image')
const publicDir = join(rootDir, 'public')
const logoPath = join(imageDir, 'logo.png')

await mkdir(imageDir, { recursive: true })

const sizes = [
  { size: 48, name: 'favicon-48.png' },
  { size: 96, name: 'favicon-96.png' },
  { size: 192, name: 'favicon-192.png' }
]

for (const { size, name } of sizes) {
  const out = join(imageDir, name)
  await sharp(logoPath)
    .resize(size, size, {
      fit: 'contain',
      background: { r: 0, g: 0, b: 0, alpha: 1 }
    })
    .png()
    .toFile(out)
  console.log(`Wrote ${name} (${size}x${size})`)
}

const favicon48 = join(imageDir, 'favicon-48.png')
await copyFile(favicon48, join(publicDir, 'favicon.ico'))
console.log('Wrote favicon.ico (48x48 PNG from logo.png)')
