const {chromium}=require('playwright-core');
const {spawn}=require('child_process');
(async()=>{
  const [,,out,from='0',to,step='1']=process.argv;
  const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium-1194/chrome-linux/chrome',args:['--allow-file-access-from-files']});
  const p=await b.newPage({viewport:{width:1920,height:1080}});
  await p.goto('file://'+__dirname+'/index.html');
  await p.waitForFunction('window.ready===true');
  const end=to?+to:await p.evaluate('TIMES.end');
  const frames=[]; for(let f=Math.round(+from*30); f<Math.round(end*30); f+=+step) frames.push(f);
  let ff=null;
  if(out.endsWith('.mp4')){
    ff=spawn('ffmpeg',['-y','-v','error','-f','image2pipe','-framerate','30','-c:v','mjpeg','-i','-','-c:v','libx264','-preset','slow','-crf','16','-pix_fmt','yuv420p','-r','30',out],{stdio:['pipe','inherit','inherit']});
  }
  for(const [k,f] of frames.entries()){
    await p.evaluate(t=>window.seek(t),f/30);
    const buf=await p.screenshot({type:'jpeg',quality:95});
    if(ff){ if(!ff.stdin.write(buf)) await new Promise(r=>ff.stdin.once('drain',r)); }
    else require('fs').writeFileSync(`${out}/${String(f).padStart(5,'0')}.jpg`,buf);
    if(k%150===0) console.log('frame',f);
  }
  if(ff){ff.stdin.end(); await new Promise(r=>ff.on('close',r));}
  await b.close();
})();
