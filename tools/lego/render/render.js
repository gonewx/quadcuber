// 用法: node render.js jobs.json [端口]
// jobs: [{"model": "文件.ldr", "out": "图.png", "opts": {...}}], 同一个浏览器会话里依次渲染。
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const fs = require('fs');
(async () => {
  const jobs = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
  const port = process.argv[3] || '8765';
  const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  const page = await browser.newPage();
  page.on('pageerror', e => console.error('页面错误:', e.message));
  await page.goto(`http://127.0.0.1:${port}/index.html`);
  await page.waitForFunction(() => window.pageReady === true, null, { timeout: 60000 });
  for (const j of jobs) {
    const text = fs.readFileSync(j.model, 'utf8');
    const url = await page.evaluate(([t, o]) => window.renderLdr(t, o), [text, j.opts || {}]);
    fs.writeFileSync(j.out, Buffer.from(url.split(',')[1], 'base64'));
  }
  await browser.close();
  console.log(`已渲染 ${jobs.length} 张图`);
})().catch(e => { console.error(e); process.exit(1); });
