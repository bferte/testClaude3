import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
import { spawn } from 'child_process';
import path from 'path';
const [mode, ...args] = process.argv.slice(2);
const browser = await chromium.launch({ args:['--allow-file-access-from-files','--disable-web-security','--force-color-profile=srgb'] });
const page = await browser.newPage({ viewport:{width:1920,height:1080}, deviceScaleFactor:1 });
page.on('console', m=>console.log('PAGE:', m.text())); page.on('pageerror', e=>console.log('ERR:', e.message));
await page.goto('file://'+path.resolve('build/index.html'));
await page.evaluate(()=>window.ready);
if (mode==='stills') {
  for (const t of args) { await page.evaluate(t=>window.render(t), +t); await page.screenshot({path:`frames/s_${t}.jpg`, type:'jpeg', quality:85}); }
} else {
  const [out, t0s, t1s] = args; const fps=30, t0=+t0s, t1=+t1s;
  const ff = spawn('ffmpeg',['-v','error','-y','-f','image2pipe','-framerate','30','-c:v','mjpeg','-i','-','-c:v','libx264','-preset','medium','-crf','17','-pix_fmt','yuv420p','-r','30',out],{stdio:['pipe','inherit','inherit']});
  const n=Math.round((t1-t0)*fps);
  for (let i=0;i<n;i++){ await page.evaluate(t=>window.render(t), t0+i/fps);
    const buf=await page.screenshot({type:'jpeg',quality:95});
    if(!ff.stdin.write(buf)) await new Promise(r=>ff.stdin.once('drain',r));
    if(i%150===0) console.log('frame',i,'/',n); }
  ff.stdin.end(); await new Promise(r=>ff.on('close',r));
}
await browser.close();
