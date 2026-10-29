const { chromium } = require('playwright');
const fs=require('fs'), path=require('path');
const VENDOR=path.resolve(__dirname,'node_modules/three');
(async()=>{
  const [,,mode,out,timesArg]=process.argv;
  const b=await chromium.launch({args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
  const pg=await b.newPage({viewport:{width:1920,height:1080}});
  pg.on('console',m=>{ if(['error','warning'].includes(m.type())) console.log('[page]',m.type(),m.text().slice(0,300)); });
  pg.on('pageerror',e=>console.log('[pageerror]',e.message));
  await pg.route('https://cdn.jsdelivr.net/npm/three@0.170.0/**', r=>{
    const rel=r.request().url().replace('https://cdn.jsdelivr.net/npm/three@0.170.0/','');
    r.fulfill({path:path.join(VENDOR,rel),contentType:'application/javascript'});
  });
  await pg.goto('http://127.0.0.1:8765/index.html?render');
  await pg.evaluate(()=>window.__ready);
  fs.mkdirSync(out,{recursive:true});
  let times;
  if(mode==='shots') times=JSON.parse(timesArg);
  else { const d=await pg.evaluate(()=>window.DURATION); times=[]; for(let f=0;f<d*30;f++) times.push(f/30); }
  const t0=Date.now();
  for(let i=0;i<times.length;i++){
    await pg.evaluate(t=>window.renderAt(t),times[i]);
    await pg.screenshot({path:`${out}/${String(i).padStart(5,'0')}.jpg`,type:'jpeg',quality:93});
    if(i%30===0||mode==='shots') console.log(i,'/',times.length,((Date.now()-t0)/(i+1)/1000).toFixed(2)+'s/frame');
  }
  await b.close();
})();
