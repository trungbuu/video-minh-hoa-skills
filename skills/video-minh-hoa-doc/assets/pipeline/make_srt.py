#!/usr/bin/env python3
"""Xuất phụ đề .srt từ cues.json, mốc lấy theo từ thật đã căn nên khớp tiếng.

python3 tools/make_srt.py renders/video.srt
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mvlib import load_json  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "renders", "video.srt")
cues = load_json(os.path.join(ROOT, "cues.json"))


def ts(x):
    ms = int(round(x * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


rows = []
for k, c in enumerate(cues["caps"]):
    a = c["w"][0][1] if c.get("w") else c["v"]
    b = min(c["b"], (c["w"][-1][2] + 0.6) if c.get("w") else c["b"])
    text = c["s"].replace("_", " ").replace(" ", " ")
    rows.append(f"{k + 1}\n{ts(a)} --> {ts(b)}\n{text}\n")
os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
open(out, "w", encoding="utf-8").write("\n".join(rows))
print(f"{out}: {len(rows)} dòng phụ đề")
