import fs from 'node:fs';
import path from 'node:path';
import sharp from 'sharp';

if (process.argv[2] === '--check') {
  console.log(JSON.stringify({node: process.version, sharp: sharp.versions.sharp}));
  process.exit(0);
}
const root = path.resolve(process.argv[2]);
const plan = JSON.parse(fs.readFileSync(path.join(root, 'render-plan.json'), 'utf8'));
const audit = [];
for (const item of plan.profiles) {
  const svg = fs.readFileSync(path.join(root, item.source));
  const [w, h] = plan.viewBox.slice(2);
  for (const size of plan.sizes) {
    // Bound both aspect ratio and diagonal for a safe circular profile crop.
    const scale = Math.min(size * .72 / w, size * .72 / h, size * .9 / Math.hypot(w, h));
    const width = Math.max(1, Math.floor(w * scale));
    const height = Math.max(1, Math.floor(h * scale));
    const mark = await sharp(svg, {density: 300}).resize(width, height, {fit: 'fill'}).png().toBuffer();
    const file = `png/${plan.slug}-${item.id}-${size}.png`;
    await sharp({create: {width: size, height: size, channels: 3, background: item.background}})
      .composite([{input: mark, gravity: 'centre'}]).removeAlpha().png().toFile(path.join(root, file));
    const meta = await sharp(path.join(root, file)).metadata();
    const {data, info} = await sharp(path.join(root, file)).raw().toBuffer({resolveWithObject: true});
    const expected = item.background.match(/[0-9a-f]{2}/gi).map(x => parseInt(x, 16));
    const corners = [0, size - 1, size * (size - 1), size * size - 1];
    if (meta.width !== size || meta.height !== size || meta.channels !== 3 || meta.hasAlpha ||
        corners.some(p => expected.some((v, c) => data[p * info.channels + c] !== v))) {
      throw Error(`Incorrect dimensions, alpha or background: ${file}`);
    }
    audit.push({file, width: size, height: size, channels: meta.channels, background: item.background,
      markWidth: width, markHeight: height, circularCropFits: Math.hypot(width, height) <= size * .9 + 1});
  }
}
for (const name of ['palette-comparison', 'profile-previews', 'mark-preview']) {
  await sharp(path.join(root, `${name}.svg`)).png().toFile(path.join(root, `${name}.png`));
}
fs.writeFileSync(path.join(root, 'raster-audit.json'), JSON.stringify(audit, null, 2) + '\n');
console.log(`Rendered and checked ${audit.length} profile PNGs and 3 preview sheets.`);
