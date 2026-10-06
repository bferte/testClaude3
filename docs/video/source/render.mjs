import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
import fs from 'fs';
const [,, html, outDir, fps='30', dur='26', only] = process.argv;
fs.mkdirSync(outDir,{recursive:true});
const b = await chromium.launch();
const pg = await b.newPage({viewport:{width:1920,height:1080}});
await pg.goto('file://'+html); await pg.evaluate(()=>document.fonts.ready);
const times = only ? only.split(',').map(Number) : [...Array(Math.round(+dur*+fps)).keys()].map(i=>i/+fps);
let i=0;
for (const t of times){
  await pg.evaluate(t=>window.render(t), t);
  const name = only ? `t${t}` : String(i).padStart(4,'0');
  await pg.screenshot({path:`${outDir}/${name}.jpg`, type:'jpeg', quality:93}); i++;
}
await b.close();
