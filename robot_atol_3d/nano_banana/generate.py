"""Génère des images clés avec Nano Banana (API Gemini) à partir des références du robot ATOL.

La clé est lue dans la variable d'environnement GEMINI_API_KEY (jamais dans le dépôt).
    GEMINI_API_KEY=... python3 generate.py <nom> "<prompt>" [modele] [ratio]
"""
import base64
import io
import json
import os
import subprocess
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REFS = [
    os.path.join(ROOT, "references", "turnaround.webp"),
    os.path.join(ROOT, "previews", "threequarter.png"),
    os.path.join(ROOT, "references", "reference_buste.png"),
]
STYLE = (
    "Use the attached images as strict character references: it is the ATOL mascot robot. Keep it exactly on-model: "
    "big round glossy white helmet head with a navy blue band on top, thick black rectangular glasses with cyan LED "
    "temples, big blue cartoon eyes, small open smile, pink cheeks, blue headphone ear pods with cyan glowing ring, "
    "royal blue t-shirt bodysuit with the white ATOL logo on the chest (exact letters A-T-O-L), white robotic arms "
    "with black joints, black and white hands, white legs with black knees, white sneakers with blue toe and heel. "
    "Premium 3D render, Pixar-like quality, soft studio lighting, clean composition for motion design. "
)


def to_part(path):
    im = Image.open(path).convert("RGBA")
    bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
    bg.alpha_composite(im)
    bg = bg.convert("RGB")
    bg.thumbnail((1024, 1024))
    buf = io.BytesIO()
    bg.save(buf, "JPEG", quality=90)
    return {"inline_data": {"mime_type": "image/jpeg", "data": base64.b64encode(buf.getvalue()).decode()}}


def generate(name, prompt, model="gemini-3-pro-image", ratio="16:9", extra_refs=()):
    parts = [to_part(p) for p in (*REFS, *extra_refs)] + [{"text": STYLE + prompt}]
    body = {"contents": [{"role": "user", "parts": parts}],
            "generationConfig": {"responseModalities": ["TEXT", "IMAGE"], "imageConfig": {"aspectRatio": ratio}}}
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    out = subprocess.run(["curl", "-sS", "--max-time", "300", "-H", "Content-Type: application/json",
                          "-H", "x-goog-api-key: " + os.environ["GEMINI_API_KEY"], url, "--data-binary", "@-"],
                         input=json.dumps(body).encode(), capture_output=True, check=True).stdout
    d = json.loads(out)
    if "error" in d:
        raise SystemExit(d["error"]["message"])
    saved = []
    for c in d.get("candidates", []):
        for p in c.get("content", {}).get("parts", []):
            data = p.get("inlineData") or p.get("inline_data")
            if data:
                path = os.path.join(HERE, f"{name}.png")
                Image.open(io.BytesIO(base64.b64decode(data["data"]))).save(path)
                saved.append(path)
            elif p.get("text"):
                print("texte:", p["text"][:200])
    print("OK" if saved else "PAS D'IMAGE", saved)


if __name__ == "__main__":
    generate(sys.argv[1], sys.argv[2], *(sys.argv[3:5]))
