# Uso: python3 render.py index.html pieza.json salida/
# Dibuja las placas/escenas con el mismo código del tablero Litoral Lab.
import sys, json, base64, os, subprocess
from playwright.sync_api import sync_playwright
html, pjson, out = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(out, exist_ok=True)
p = json.load(open(pjson))
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    pg = b.new_page()
    pg.goto("file://" + os.path.abspath(html))
    pg.wait_for_function("typeof imagenes==='function'")
    pg.evaluate("document.fonts.ready")
    urls = pg.evaluate("async p=>await imagenes(p)", p)
    b.close()
files = []
for i, u in enumerate(urls, 1):
    f = os.path.join(out, f"{p['id']}-{i:02d}.png")
    open(f, "wb").write(base64.b64decode(u.split(",")[1]))
    j = f[:-4] + ".jpg"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f, "-q:v", "2", j], check=True)
    files.append(j)
if p.get("formato") == "reel":
    seg = 3.0; n = len(files)
    inputs = sum([["-loop", "1", "-t", str(seg), "-i", f] for f in files], [])
    fl = ""; last = "[0:v]"
    for k in range(1, n):
        lab = f"[x{k}]"
        fl += f"{last}[{k}:v]xfade=transition=fade:duration=0.5:offset={k*(seg-0.5):.2f}{lab};"
        last = lab
    fl += f"{last}format=yuv420p,scale=1080:1920[v]"
    dur = n * seg - (n - 1) * 0.5
    mp4 = os.path.join(out, f"{p['id']}.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-f", "lavfi", "-t", f"{dur:.2f}", "-i", "anullsrc=r=44100:cl=stereo",
                    "-filter_complex", fl, "-map", "[v]", "-map", f"{n}:a", "-c:v", "libx264", "-r", "30", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-shortest", "-movflags", "+faststart", mp4], check=True)
    files = [mp4]
print(json.dumps(files))
