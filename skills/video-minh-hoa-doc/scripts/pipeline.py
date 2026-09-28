#!/usr/bin/env python3
"""Chạy trọn chuỗi dựng video cho một dự án tạo bằng scripts/new_project.py.

python3 scripts/pipeline.py <dự án>                         -> từ đầu tới cổng nghiệm thu
python3 scripts/pipeline.py <dự án> --from layout            -> chạy lại từ bước layout (đổi mốc, không đổi lời)
python3 scripts/pipeline.py <dự án> --to eval                -> dừng sau tự soát, chưa render
python3 scripts/pipeline.py <dự án> --name ten-video --social

Các bước theo thứ tự, mỗi bước ghi file cho bước sau đọc nên không đảo thứ tự:
  check    scripts/check_script.py  giới hạn chữ, neo, thời lượng ước tính
  voice    tools/make_voice.py      lời đọc từng dòng
  align    tools/align_words.py     mốc từng từ
  layout   tools/layout.py          xếp cảnh theo phách, neo cue, cụm phụ đề -> cues.json
  audio    tools/make_audio.py      nhạc, SFX, duck, master -14 LUFS
  balance  tools/measure_mix.py     nhạc thấp hơn lời 4 đến 6 dB
  beats    hyperframes beats        đo phách của stem nhạc
  data     tools/build_data.py      data.js
  lint     hyperframes lint
  eval     tools/self_eval.py       tự soát DOM và tấm ghép khung
  render   tools/render.py          render, remux, bản không lời
  srt      tools/make_srt.py
  qa       scripts/qa_video.py      cổng nghiệm thu
Bảng “đổi gì chạy lại từ đâu” nằm trong SKILL.md.
"""
import argparse, json, os, re, subprocess, sys

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STEPS = ["check", "voice", "align", "layout", "audio", "balance", "beats", "data", "lint", "eval", "render", "srt", "qa"]
ap = argparse.ArgumentParser()
ap.add_argument("project")
ap.add_argument("--from", dest="start", choices=STEPS, default="check")
ap.add_argument("--to", dest="stop", choices=STEPS, default="qa")
ap.add_argument("--name", default=None)
ap.add_argument("--style", default=None)
ap.add_argument("--social", action="store_true")
ap.add_argument("--soft", action="store_true", help="không dừng khi balance hoặc eval báo lỗi, chỉ ghi lại")
a = ap.parse_args()
P = os.path.abspath(a.project)
name = a.name or re.sub(r"[^a-z0-9-]+", "-", os.path.basename(P).lower()).strip("-")
ENV = {**os.environ, "HYPERFRAMES_SKIP_SKILLS": "1"}
HF = ["npx", "--yes", "hyperframes@0.8.75"]


def size():
    s = open(os.path.join(P, "index.html"), encoding="utf-8").read()
    return re.search(r'id="root"[^>]*data-width="(\d+)"', s).group(1) + "x" + re.search(r'id="root"[^>]*data-height="(\d+)"', s).group(1)


CMD = {
    "check": [sys.executable, os.path.join(SKILL, "scripts", "check_script.py"), P],
    "voice": [sys.executable, "tools/make_voice.py"],
    "align": [sys.executable, "tools/align_words.py"],
    "layout": [sys.executable, "tools/layout.py"],
    "audio": [sys.executable, "tools/make_audio.py"],
    "balance": [sys.executable, "tools/measure_mix.py"],
    "beats": HF + ["beats", "."],
    "data": [sys.executable, "tools/build_data.py"],
    "lint": HF + ["lint", "."],
    "eval": [sys.executable, "tools/self_eval.py"] + (["--style", a.style] if a.style else []),
    "render": [sys.executable, "tools/render.py", "--name", name] + (["--style", a.style] if a.style else []) + (["--social"] if a.social else []),
    "srt": [sys.executable, "tools/make_srt.py", f"renders/{name}.srt"],
}
soft = {"balance", "eval"} if a.soft else set()
i0, i1 = STEPS.index(a.start), STEPS.index(a.stop)
for st in STEPS[i0:i1 + 1]:
    print(f"\n==> {st}", flush=True)
    if st == "qa":
        wh = size()
        vids = [os.path.join(P, "renders", f"{name}_{wh}_giong-doc.mp4"), os.path.join(P, "renders", f"{name}_{wh}_khong-loi.mp4")]
        cmd = [sys.executable, os.path.join(SKILL, "scripts", "qa_video.py"), *[v for v in vids if os.path.exists(v)],
               "--size", wh, "--fps", "30", "--project", P, "--srt", os.path.join(P, "renders", f"{name}.srt")]
    else:
        cmd = CMD[st]
    r = subprocess.run(cmd, cwd=P, env=ENV)
    if r.returncode != 0:
        if st in soft:
            print(f"   {st} chưa đạt, ghi nhận và chạy tiếp vì --soft")
            continue
        sys.exit(f"Dừng ở bước {st} (mã {r.returncode}). Sửa rồi chạy lại với --from {st}.")
print("\nXong chuỗi", a.start, "→", a.stop)
