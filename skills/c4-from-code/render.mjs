// Render an SVG to PNG for the look gate. Needs only a prebuilt package, in a scratch dir:
//   npm init -y >/dev/null && npm install @resvg/resvg-js@2.6.2
//   node render.mjs in.svg out.png
import { readFileSync, writeFileSync } from 'node:fs';
import { Resvg } from '@resvg/resvg-js';

const [, , input, output] = process.argv;
if (!input || !output) {
  console.error('usage: node render.mjs in.svg out.png');
  process.exit(1);
}
const svg = readFileSync(input, 'utf8');
const png = new Resvg(svg, { fitTo: { mode: 'width', value: 1600 } }).render().asPng();
writeFileSync(output, png);
console.log('rendered', input, '->', output, png.length, 'bytes');
