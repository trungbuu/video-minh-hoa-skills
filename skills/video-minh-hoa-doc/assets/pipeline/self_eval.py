#!/usr/bin/env python3
"""Bước 6 và 8 của chuỗi v2: tự soát trước khi đưa người dùng xem. Lấy ý từ vòng self-eval của video-use.

python3 tools/self_eval.py                          -> soát trang (trước khi render), ảnh review/self-eval.png
python3 tools/self_eval.py --video renders/x.mp4    -> soát khung của bản đã render, ghép dạng sóng của chính file đó

Hai phần:
1. Soát DOM ở mọi mốc quan trọng (giữa mỗi cảnh, giữa mỗi cụm phụ đề, ngay sau mỗi SFX, thẻ kết):
   chữ lọt vùng an toàn của khổ dọc (220 px trên, 470 px dưới, cột phải x > 950 trong đoạn y 880 đến 1450),
   chữ tràn khung, chữ ra ngoài khung hình, chữ đè lên phụ đề, phông chưa nạp (rơi về phông hệ thống),
   từ ghép tiếng Việt bị ngắt giữa hai âm tiết theo danh sách của vi-type.js.
   Phần tử có data-safe="ignore" được bỏ qua vùng an toàn (ví dụ logo đầu trang đã tính sẵn).
2. Tấm ghép khung hình, mỗi ô ghi mốc thời gian, ô có lỗi viền đỏ; dưới cùng là dạng sóng tiếng
   với vạch cắt cảnh (xám), SFX (đỏ) và đầu cụm phụ đề (xanh), để thấy SFX có rơi đúng khung va chạm không.

Trả mã lỗi 1 khi còn lỗi. Quy tắc làm việc: sửa rồi chạy lại, tối đa 3 vòng, quá 3 vòng thì báo người dùng kèm danh sách lỗi.
"""
import argparse, json, os, subprocess, sys, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mvlib import read_mono, load_json, save_json  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

JS_CHECK = r"""
(t) => {
  window.renderAt(t);
  const root = document.getElementById('root'), R = root.getBoundingClientRect();
  const W = R.width, H = R.height, portrait = H > W, out = [];
  const alpha = (el) => { let o = 1, n = el; while (n && n !== document.body) { const cs = getComputedStyle(n);
      if (cs.display === 'none' || cs.visibility === 'hidden') return 0; o *= parseFloat(cs.opacity || 1); n = n.parentElement; } return o; };
  const hasText = (el) => [...el.childNodes].some((n) => n.nodeType === 3 && n.nodeValue.trim());
  const els = [...root.querySelectorAll('*')].filter((el) => !(el instanceof SVGElement) && hasText(el) && alpha(el) > 0.5);
  const box = (el) => { const b = el.getBoundingClientRect(); return { l: b.left - R.left, t: b.top - R.top, r: b.right - R.left, b: b.bottom - R.top, w: b.width, h: b.height }; };
  const name = (el) => (el.id ? '#' + el.id : el.className ? '.' + String(el.className).split(' ')[0] : el.tagName.toLowerCase()) + ' “' + el.textContent.trim().slice(0, 28) + '”';
  const cap = document.getElementById('caption');
  const capBox = cap && alpha(cap) > 0.5 && cap.textContent.trim() ? box(cap) : null;
  const fams = new Set();
  for (const el of els) {
    const b = box(el); if (b.w < 2 || b.h < 2) continue;
    const ign = el.closest('[data-safe="ignore"]');
    const ecs = getComputedStyle(el);
    fams.add(ecs.fontWeight + '|' + ecs.fontStyle + '|' + ecs.fontFamily.split(',')[0].replace(/["']/g, '').trim() + '|' + el.textContent.trim().slice(0, 24));
    if (b.l < -2 || b.r > W + 2 || b.t < -2 || b.b > H + 2) out.push(['RA NGOÀI KHUNG', name(el)]);
    if (portrait && !ign) {
      if (b.t < 220 - 2) out.push(['VÙNG AN TOÀN TRÊN', name(el)]);
      if (b.b > H - 470 + 2) out.push(['VÙNG AN TOÀN DƯỚI', name(el)]);
      if (b.r > 950 && b.t < 1450 && b.b > 880) out.push(['CỘT PHẢI BỊ NÚT CHE', name(el)]);
    }
    const cs = getComputedStyle(el);
    if (cs.display !== 'inline' && el.scrollWidth > el.clientWidth + 2 && cs.overflow !== 'visible') out.push(['TRÀN CHỮ', name(el)]);
    if (capBox && !cap.contains(el) && !el.contains(cap)) {
      // so với khối có nền màu bao quanh chữ (thẻ, banner), vì phụ đề đè lên nền cũng khó đọc như đè lên chữ
      let host = el, bb = b;
      for (let n = el; n && n !== root && !n.contains(cap); n = n.parentElement) {
        const c2 = getComputedStyle(n);
        if ((c2.backgroundColor && !/rgba\(0, 0, 0, 0\)|transparent/.test(c2.backgroundColor)) || c2.backgroundImage !== 'none') { host = n; bb = box(n); }
      }
      const ix = Math.min(bb.r, capBox.r) - Math.max(bb.l, capBox.l), iy = Math.min(bb.b, capBox.b) - Math.max(bb.t, capBox.t);
      if (ix > 4 && iy > 4) out.push(['ĐÈ PHỤ ĐỀ', name(el)]);
    }
  }
  // kiểm đúng độ đậm, kiểu và chữ đang hiển thị, vì phông chia theo unicode-range và theo độ đậm
  for (const k of fams) { const [w, st, f, sample] = k.split('|');
    if (f && !/^(serif|sans-serif|monospace|system-ui)$/i.test(f) && !document.fonts.check(`${st} ${w} 32px "${f}"`, sample || ' ')) out.push(['PHÔNG CHƯA NẠP', `${f} ${w}`]); }
  // từ ghép bị tách giữa hai âm tiết
  const P = (window.viType && window.viType.pairs) || [];
  if (P.length) {
    const LET = 'A-Za-zÀ-ỹĐđ';
    const RE = new RegExp('(?<![' + LET + '])(' + P.map((x) => x.replace(/ /g, '[\\s\\u00A0]')).join('|') + ')(?![' + LET + '])', 'giu');
    const rg = document.createRange();
    for (const el of els) {
      let prev = null, text = '', pos = [];
      for (const n of el.childNodes) { if (n.nodeType !== 3) continue; const s = n.nodeValue;
        for (let i = 0; i < s.length; i++) { rg.setStart(n, i); rg.setEnd(n, i + 1); const bb = rg.getBoundingClientRect();
          if (bb.height) { if (prev !== null && Math.abs(bb.top - prev) > 2) pos.push(text.length + i); prev = bb.top; } }
        text += s; }
      for (const m of text.matchAll(RE)) for (const p of pos) if (p > m.index && p < m.index + m[0].length) out.push(['TÁCH TỪ GHÉP', m[0]]);
    }
  }
  return out;
}
"""


def sample_times(C):
    ts = []
    sc = C["scenes"] + [C["duration"]]
    ts += [round((sc[k] + sc[k + 1]) / 2, 2) for k in range(len(C["scenes"]))]
    ts += [round((c["a"] + c["b"]) / 2, 2) for c in C["caps"]]
    ts += [round(h + 0.35, 2) for h in C.get("hits", [])]
    ts += [round(min(C["duration"] - 0.2, C["ending"] + 2.0), 2)]
    return sorted({t for t in ts if 0 <= t < C["duration"]})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", default=None)
    ap.add_argument("--style", default="")
    ap.add_argument("--cols", type=int, default=8)
    a = ap.parse_args()
    C = load_json(os.path.join(ROOT, "cues.json"))
    times = sample_times(C)
    from playwright.sync_api import sync_playwright
    from PIL import Image, ImageDraw, ImageFont
    issues, shots = {}, {}
    tmp = tempfile.mkdtemp()
    with sync_playwright() as p:
        b = p.chromium.launch()
        html = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
        import re
        W = int(re.search(r'id="root"[^>]*data-width="(\d+)"', html).group(1)); H = int(re.search(r'id="root"[^>]*data-height="(\d+)"', html).group(1))
        pg = b.new_page(viewport={"width": W, "height": H})
        logs = []
        pg.on("console", lambda m: logs.append(m.text) if m.type in ("warning", "error") else None)
        pg.on("pageerror", lambda e: logs.append("LỖI JS: " + str(e)))
        pg.goto("file://" + os.path.join(ROOT, "index.html") + (f"?style={a.style}" if a.style else ""))
        pg.wait_for_function("typeof window.renderAt === 'function'", polling=100)
        pg.evaluate("Promise.race([document.fonts.ready, new Promise(r => setTimeout(r, 4000))])")
        pg.wait_for_timeout(300)
        for t in times:
            res = pg.evaluate(JS_CHECK, t)
            if res:
                issues[t] = sorted({f"{k}: {v}" for k, v in res})
            if not a.video:
                f = os.path.join(tmp, f"{t:.2f}.png"); pg.locator("#root").screenshot(path=f); shots[t] = f
        b.close()
    # neo W() không tìm thấy từ hay lỗi JS là lỗi của cả video, không gắn với mốc nào
    glob = sorted({x for x in logs if "không thấy" in x or x.startswith("LỖI JS")})
    if glob:
        issues[-1.0] = [f"NEO HOẶC JS: {x}" for x in glob]
    if a.video:
        for t in times:
            f = os.path.join(tmp, f"{t:.2f}.png")
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", a.video, "-frames:v", "1", f], check=True)
            shots[t] = f
    # tấm ghép
    tw = 216; th = int(tw * H / W); cols = min(a.cols, len(times)); rows = (len(times) + cols - 1) // cols
    wave_h = 170
    sheet = Image.new("RGB", (cols * tw + (cols + 1) * 8, rows * (th + 30) + 8 + wave_h + 20), "white")
    d = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 15)
    except OSError:
        font = ImageFont.load_default()
    for k, t in enumerate(times):
        x = 8 + (k % cols) * (tw + 8); y = 8 + (k // cols) * (th + 30)
        im = Image.open(shots[t]).convert("RGB").resize((tw, th))
        sheet.paste(im, (x, y))
        col = (217, 54, 68) if t in issues else (200, 200, 200)
        d.rectangle([x - 2, y - 2, x + tw + 1, y + th + 1], outline=col, width=3 if t in issues else 1)
        d.text((x, y + th + 6), f"{t:.2f}s" + ("  LỖI" if t in issues else ""), fill=col if t in issues else (60, 60, 60), font=font)
    # dạng sóng và mốc
    audio = a.video or os.path.join(ROOT, "audio", "mix.wav")
    y0 = 8 + rows * (th + 30) + 6; ww = sheet.width - 16
    try:
        sig = read_mono(audio, 8000)
        import numpy as np
        n = len(sig); cols_px = np.array_split(np.abs(sig), ww)
        peak = max(1e-9, float(np.max(np.abs(sig))))
        for i, c in enumerate(cols_px):
            h = (float(c.max()) if len(c) else 0) / peak * (wave_h / 2 - 6)
            d.line([(8 + i, y0 + wave_h / 2 - h), (8 + i, y0 + wave_h / 2 + h)], fill=(120, 120, 120))
    except Exception as e:  # noqa: BLE001
        d.text((8, y0), f"không đọc được tiếng: {e}", fill=(200, 0, 0), font=font)
    X = lambda t: 8 + ww * t / C["duration"]  # noqa: E731
    for s in C["scenes"]:
        d.line([(X(s), y0), (X(s), y0 + wave_h)], fill=(170, 170, 170), width=2)
    for c in C["caps"]:
        d.line([(X(c["v"]), y0 + wave_h - 18), (X(c["v"]), y0 + wave_h)], fill=(40, 110, 220), width=2)
    for h in C.get("sfx", []):
        d.line([(X(h["t"]), y0), (X(h["t"]), y0 + 22)], fill=(217, 54, 68), width=3)
    for t in times:
        d.ellipse([X(t) - 3, y0 + wave_h + 4, X(t) + 3, y0 + wave_h + 10], fill=(217, 54, 68) if t in issues else (60, 60, 60))
    os.makedirs(os.path.join(ROOT, "review"), exist_ok=True)
    out = os.path.join(ROOT, "review", "self-eval.png"); sheet.save(out)
    save_json({"times": times, "issues": {f"{k:.2f}": v for k, v in issues.items()}}, os.path.join(ROOT, "review", "self-eval.json"))
    print(f"{len(times)} mốc soát, {len(issues)} mốc có lỗi. Ảnh: {os.path.relpath(out, ROOT)}")
    for t, v in issues.items():
        for x in v:
            print(f"  {t:6.2f}s  {x}")
    sys.exit(1 if issues else 0)


if __name__ == "__main__":
    main()
