"""Génère les textures utilisées par build_robot.py (Python 3 + Pillow, potrace).

    python3 make_textures.py
"""
import math
import os
import random
import subprocess

from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, "textures")
os.makedirs(TEX, exist_ok=True)

# logo ATOL : PNG officiel -> SVG vectoriel (potrace)
logo = Image.open(os.path.join(HERE, "references", "atol_logo.png")).convert("RGBA")
pbm = os.path.join(TEX, "atol_logo.pbm")
logo.split()[3].point(lambda v: 0 if v > 128 else 255).convert("1").save(pbm)
subprocess.run(["potrace", "-s", "-o", os.path.join(TEX, "atol_logo.svg"), pbm], check=True)
os.remove(pbm)

# iris : dégradé radial cyan -> bleu -> marine, stries, grosse pupille
N = 512
im = Image.new("RGB", (N, N))
px = im.load()
random.seed(3)
streaks = [random.random() for _ in range(720)]


def lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


navy, blue, cyan, pupil = (6, 22, 64), (18, 98, 214), (92, 205, 255), (4, 8, 20)
for y in range(N):
    for x in range(N):
        dx, dy = (x - N / 2) / (N / 2), (y - N / 2) / (N / 2)
        r, a = math.hypot(dx, dy), math.atan2(dy, dx)
        if r < 0.34:
            c = pupil
        elif r < 0.40:
            c = lerp(pupil, (10, 50, 120), (r - 0.34) / 0.06)
        elif r < 0.86:
            t = (r - 0.40) / 0.46
            c = lerp(cyan, blue, min(1, t * 1.3)) if t < 0.77 else lerp(blue, navy, (t - 0.77) / 0.23)
            k = 0.82 + 0.3 * streaks[int((a + math.pi) / (2 * math.pi) * 720) % 720] * (1 - abs(t - 0.5))
            c = tuple(min(255, ch * k) for ch in c)
            if dy > 0.15:  # bas de l'iris plus lumineux
                c = tuple(min(255, ch * 1.12) for ch in c)
        else:
            c = navy
        px[x, y] = tuple(int(v) for v in c)
im.filter(ImageFilter.GaussianBlur(1.2)).save(os.path.join(TEX, "iris.png"))
print("textures OK")
