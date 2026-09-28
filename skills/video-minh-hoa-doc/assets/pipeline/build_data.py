#!/usr/bin/env python3
"""Bước 5 của chuỗi v2: gộp phách, cues và đường bao lời thành data.js cho cảnh đọc.

HYPERFRAMES_SKIP_SKILLS=1 npx hyperframes beats . && python3 tools/build_data.py

Có beats/audio/music.wav.json thì dùng phách đo được, không có thì dựng lưới từ bpm và beat0.
Đồng bộ data-duration trong index.html với cues.json.
"""
import json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mvlib import load_json  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cues = load_json(os.path.join(ROOT, "cues.json"))
cues.pop("_ghichu", None)
bj = load_json(os.path.join(ROOT, "beats", "audio", "music.wav.json"))
if bj:
    beats = [[round(b["time"], 3), round(b["strength"], 3)] for b in bj["beats"]]
else:
    step = 60 / cues["bpm"]; k = 0; beats = []
    while cues["beat0"] + k * step < cues["duration"]:
        beats.append([round(cues["beat0"] + k * step, 3), 0.8 if k % 4 == 0 else 0.5]); k += 1
env = (load_json(os.path.join(ROOT, "audio", "vo-env.json"), {}) or {}).get("env", [])
out = "// Tự sinh bởi tools/build_data.py, không sửa tay.\n"
out += "window.BEATS = " + json.dumps(beats) + ";\n"
out += "window.CUES = " + json.dumps(cues, ensure_ascii=False) + ";\n"
out += "window.ENV = " + json.dumps(env) + ";\n"
script = load_json(os.path.join(ROOT, "script.json"), {}) or {}
out += "window.SCENES = " + json.dumps(script.get("scenes", []), ensure_ascii=False) + ";\n"
out += "window.META = " + json.dumps(script.get("meta", {}), ensure_ascii=False) + ";\n"
open(os.path.join(ROOT, "data.js"), "w", encoding="utf-8").write(out)
p = os.path.join(ROOT, "index.html"); s = open(p, encoding="utf-8").read()
s = re.sub(r'data-duration="[\d.]+"', f'data-duration="{cues["duration"]}"', s)
open(p, "w", encoding="utf-8").write(s)
print(f"data.js: {len(beats)} phách{' (đo)' if bj else ' (lưới)'}, {len(cues['caps'])} cụm phụ đề, {len(env)} khung đường bao."
      f" index.html: data-duration = {cues['duration']}")
