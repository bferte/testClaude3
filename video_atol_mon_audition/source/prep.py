import subprocess, os, shutil, glob
B='build/assets'
def seq(name, src, segs, crop, w):
    d=f'{B}/{name}'; shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
    n=0
    for i,(a,b,sp) in enumerate(segs):
        tmp=f'{d}/_s{i}'; os.makedirs(tmp)
        cw,ch,cx,cy=crop
        subprocess.run(['ffmpeg','-v','error','-ss',str(a),'-t',str(b-a),'-i',src,'-vf',
          f'crop={cw}:{ch}:{cx}:{cy},setpts=PTS/{sp},fps=30,scale={w}:-2:flags=lanczos','-q:v','3',f'{tmp}/%05d.jpg'],check=True)
        for f in sorted(glob.glob(f'{tmp}/*.jpg')):
            n+=1; os.rename(f, f'{d}/{n:05d}.jpg')
        os.rmdir(tmp)
    print(name, n, 'frames', n/30, 's')
# infos + calibrage (scene B)
#seq('infos','src/v1.mp4',[(0.0,3.6,1),(6.6,8.4,1),(8.5,11.1,1)],(740,550,590,250),1110)
# keypad (scene C)
seq('keypad','src/v1.mp4',[(13.3,16.4,1.1),(16.4,19.6,1)],(740,800,590,60),888)
#seq('keypad2','src/v2.mp4',[(0.9,2.9,1),(3.4,5.8,1.5),(5.8,7.9,1)],(740,800,596,62),888)
# result (scene D)
#seq('result','src/v2.mp4',[(8.2,14.3,1)],(1420,810,0,95),1420)
