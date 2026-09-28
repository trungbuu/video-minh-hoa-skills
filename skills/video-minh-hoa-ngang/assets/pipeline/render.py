#!/usr/bin/env python3
"""Bước 7 của chuỗi v2: render bằng HyperFrames rồi thay tiếng bằng bản master gốc (remux).

python3 tools/render.py --name ten-video                     -> renders/<name>_<W>x<H>_giong-doc.mp4 và _khong-loi.mp4
python3 tools/render.py --name x --style comic --social       -> thêm bản nén _social.mp4 để đăng mạng xã hội
python3 tools/render.py --name x --styles flat,neon           -> nhiều phong cách trong một lần (--batch)

Vì sao phải remux: bộ render mã hoá lại AAC và đỉnh thật có thể vượt -1 dBFS, khi đó HyperFrames tự hạ cả bản.
Bản v1 né bằng cách master ở -3 dBTP và -16 LUFS nên video nghe nhỏ hơn video khác trên Reels.
Bản v2 master -14 LUFS, -1,5 dBTP, render xong thì bỏ luồng tiếng của renderer và mã hoá thẳng từ mix.wav
đúng một lần. Kỹ thuật này lấy từ motion-video (bestagentkits).
Máy thiếu ffprobe thì chuyển sang bộ render Playwright dự phòng như v1.
"""
import argparse, json, os, re, shutil, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mvlib import ff, measure  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HF = ["npx", "--yes", "hyperframes@0.8.75"]
ENV = {**os.environ, "HYPERFRAMES_SKIP_SKILLS": "1"}


def size():
    s = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    w = re.search(r'id="root"[^>]*data-width="(\d+)"', s); h = re.search(r'id="root"[^>]*data-height="(\d+)"', s)
    return int(w.group(1)), int(h.group(1))


def render_playwright(style, out, W, H, fps=30):
    from playwright.sync_api import sync_playwright
    dur = json.load(open(os.path.join(ROOT, "cues.json"), encoding="utf-8"))["duration"]
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={"width": W, "height": H})
        pg.goto("file://" + os.path.join(ROOT, "index.html") + "?style=" + style)
        pg.wait_for_function("typeof window.renderAt === 'function'", polling=100)
        pg.evaluate("Promise.race([document.fonts.ready, new Promise(r => setTimeout(r, 3000))])")
        enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "image2pipe", "-framerate", str(fps), "-c:v", "png", "-i", "-",
                                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "16", "-preset", "medium", out], stdin=subprocess.PIPE)
        root = pg.locator("#root")
        for i in range(int(round(fps * dur))):
            pg.evaluate(f"window.renderAt({i / fps})"); enc.stdin.write(root.screenshot(type="png"))
        enc.stdin.close(); enc.wait(); b.close()


def remux(video, audio, out, ceiling=-1.2):
    """Ghép hình của renderer với tiếng master, mã hoá AAC đúng một lần. AAC có thể đẩy đỉnh thật lên
    (SFX có sườn dốc hay bị), nên đo lại sau khi mã hoá; vượt trần thì chặn đỉnh thấp hơn đúng phần vượt rồi mã hoá lại."""
    src, tmp = audio, None
    for _ in range(4):
        ff("-i", video, "-i", src, "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
           "-ar", "48000", "-ac", "2", "-shortest", "-movflags", "+faststart", out)
        lufs, tp = measure(out)
        if tp <= ceiling:
            break
        over = tp - ceiling + 0.2
        tmp = out + ".lim.wav"
        cur = measure(src)[1]
        lim = 10 ** ((cur - over) / 20)
        ff("-i", src, "-af", f"aresample=192000,alimiter=limit={lim:.4f}:level=0:attack=0.5:release=40,aresample=48000",
           "-c:a", "pcm_s24le", tmp + ".x.wav")
        os.replace(tmp + ".x.wav", tmp); src = tmp
    if tmp and os.path.exists(tmp):
        os.remove(tmp)
    lufs, tp = measure(out)
    print(f"  {os.path.basename(out)}: {lufs:.1f} LUFS, đỉnh thật {tp:.1f} dBTP sau khi mã hoá AAC")


def social(src, out):
    ff("-i", src, "-c:v", "libx264", "-preset", "slow", "-crf", "21", "-maxrate", "6M", "-bufsize", "12M", "-pix_fmt", "yuv420p",
       "-profile:v", "high", "-level", "4.1", "-g", "60", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", default="video")
    ap.add_argument("--style", default=None)
    ap.add_argument("--styles", default=None)
    ap.add_argument("--social", action="store_true")
    ap.add_argument("--quality", default="high")
    a = ap.parse_args()
    W, H = size()
    out = os.path.join(ROOT, "renders"); os.makedirs(out, exist_ok=True)
    styles = a.styles.split(",") if a.styles else [a.style] if a.style else [None]
    raws = {}
    if shutil.which("ffprobe"):
        if len(styles) > 1 or styles[0]:
            rows = os.path.join(out, "_rows.json")
            json.dump([{"style": s} for s in styles], open(rows, "w"))
            subprocess.run(HF + ["render", ".", "--batch", rows, "--output", "renders/_raw_{style}.mp4", "--strict-variables",
                                 "--quality", a.quality, "--quiet"], cwd=ROOT, env=ENV, check=True)
            os.remove(rows)
            raws = {s: os.path.join(out, f"_raw_{s}.mp4") for s in styles}
        else:
            raw = os.path.join(out, "_raw.mp4")
            subprocess.run(HF + ["render", ".", "--output", "renders/_raw.mp4", "--quality", a.quality, "--quiet"], cwd=ROOT, env=ENV, check=True)
            raws = {None: raw}
    else:
        print("Chưa có ffprobe, dùng bộ render Playwright dự phòng.")
        for s in styles:
            raws[s] = os.path.join(out, f"_raw_{s or 'mac-dinh'}.mp4"); render_playwright(s or "", raws[s], W, H)
    made = []
    for s, raw in raws.items():
        base = f"{a.name}{'_' + s if s and len(styles) > 1 else ''}_{W}x{H}"
        v = os.path.join(out, base + "_giong-doc.mp4"); remux(raw, os.path.join(ROOT, "audio", "mix.wav"), v); made.append(v)
        if os.path.exists(os.path.join(ROOT, "audio", "bed.wav")):
            k = os.path.join(out, base + "_khong-loi.mp4"); remux(raw, os.path.join(ROOT, "audio", "bed.wav"), k); made.append(k)
        if a.social:
            so = os.path.join(out, base + "_social.mp4"); social(v, so); made.append(so)
        os.remove(raw)
    print("xong:\n  " + "\n  ".join(os.path.relpath(m, ROOT) for m in made))


if __name__ == "__main__":
    main()
