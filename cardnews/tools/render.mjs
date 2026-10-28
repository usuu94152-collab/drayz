// 카드뉴스 HTML 검사 + JPG 저장
//   node tools/render.mjs 결과.html 출력폴더 [--jpg]
//   → 출력폴더/preview.png (전체 모아보기), 카드별 넘침 보고, --jpg 면 1080×1350 JPG
import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';
import { fileURLToPath, pathToFileURL } from 'url';

const here = path.dirname(fileURLToPath(import.meta.url));
const vendor = path.join(here, 'vendor');
const [file, outdir = 'out', ...flags] = process.argv.slice(2);
if (!file) { console.error('사용법: node tools/render.mjs 결과.html 출력폴더 [--jpg]'); process.exit(1); }
if (!fs.existsSync(path.join(vendor, 'pretendard'))) { console.error('먼저 bash tools/setup.sh 를 실행하세요.'); process.exit(1); }
fs.mkdirSync(outdir, { recursive: true });

const root = execSync('npm root -g').toString().trim();
const { chromium } = await import(pathToFileURL(path.join(root, 'playwright', 'index.mjs')).href);
const browser = await chromium.launch(fs.existsSync('/opt/pw-browsers/chromium') ? { executablePath: '/opt/pw-browsers/chromium' } : {});
const page = await browser.newPage({ viewport: { width: 1600, height: 1200 }, deviceScaleFactor: 1.5 });
const errors = [];
page.on('pageerror', e => errors.push(e.message));
const H = { 'Access-Control-Allow-Origin': '*' };
await page.route(/jsdelivr/, route => {
  const u = route.request().url();
  if (u.includes('html-to-image')) return route.fulfill({ path: path.join(vendor, 'html-to-image/dist/html-to-image.js'), headers: H, contentType: 'application/javascript' });
  if (u.endsWith('.woff2')) return route.fulfill({ path: path.join(vendor, 'pretendard/dist/web/variable/woff2/PretendardVariable.woff2'), headers: H, contentType: 'font/woff2' });
  return route.fulfill({ path: path.join(vendor, 'pretendard/dist/web/variable/pretendardvariable.css'), headers: H, contentType: 'text/css' });
});
await page.goto(pathToFileURL(path.resolve(file)).href);
await page.evaluate(() => document.body.classList.remove('single-view'));
await page.evaluate(() => document.fonts.ready);
await page.waitForTimeout(500);
await page.locator('#gallery').screenshot({ path: path.join(outdir, 'preview.png') });

// 넘침 검사: 카드 밖으로 나간 글, 위 글과 아래 사진/칸이 겹치는지, 로고와 본문 간격
const report = await page.evaluate(() => [...document.querySelectorAll('#gallery .card')].map((card, i) => {
  const r = card.getBoundingClientRect(); let out = 0;
  card.querySelectorAll('[data-path],figure,.mini-features,.options-grid,.tags,.features').forEach(el => {
    const q = el.getBoundingClientRect(); out = Math.max(out, q.bottom - r.bottom, r.top - q.top, q.right - r.right, r.left - q.left);
  });
  const copy = card.querySelector('.gallery-copy,.options-copy');
  const below = card.querySelector('.photo-grid,.bottom-photo');
  const clash = copy && below ? copy.getBoundingClientRect().bottom - below.getBoundingClientRect().top : -1;
  const top = card.querySelector('.slide-top')?.getBoundingClientRect();
  const first = card.querySelector('.gallery-copy,.options-copy,.bottom-copy,.cover-copy,.closing-copy,.photo-caption,.map')?.getBoundingClientRect();
  const gap = top && first ? first.top - top.bottom : 99;
  const problems = [];
  if (out > 0.5) problems.push(`카드 밖으로 ${out.toFixed(0)}px 넘침`);
  if (clash > 0) problems.push(`글과 아래 사진이 ${clash.toFixed(0)}px 겹침`);
  if (gap < 4) problems.push('로고/번호와 본문이 너무 붙음');
  const empty = card.querySelectorAll('.scene-photo.empty').length;
  if (empty) problems.push(`빈 사진 ${empty}곳`);
  return `${String(i + 1).padStart(2, '0')} ${problems.length ? '⚠ ' + problems.join(', ') : 'OK'}`;
}).join('\n'));
console.log(report);

if (flags.includes('--jpg')) {
  await page.setViewportSize({ width: 1300, height: 1000 });
  await page.click('#save-jpg');
  await page.waitForFunction(() => /완료|문제/.test(document.querySelector('.export-status').textContent), null, { timeout: 180000 });
  const files = await page.evaluate(async () => Promise.all([...document.querySelectorAll('.export-grid figure')].map(async f => {
    const blob = await (await fetch(f.querySelector('img').src)).blob();
    const reader = new FileReader();
    return new Promise(res => { reader.onload = () => res({ name: f.querySelector('a').download, data: reader.result.split(',')[1] }); reader.readAsDataURL(blob); });
  })));
  for (const f of files) fs.writeFileSync(path.join(outdir, f.name), Buffer.from(f.data, 'base64'));
  console.log(`JPG ${files.length}장 → ${outdir}`);
}
if (errors.length) console.log('페이지 오류:', errors.join(' | '));
await browser.close();
