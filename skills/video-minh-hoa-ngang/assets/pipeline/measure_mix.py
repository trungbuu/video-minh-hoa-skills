#!/usr/bin/env python3
"""Đo cân bằng nhạc và lời từ stem do tools/make_audio.py xuất ra, thay vì tin tai trên loa laptop.

python3 tools/measure_mix.py                 -> in bảng và trả mã lỗi 1 nếu lệch đích
python3 tools/measure_mix.py --target 5 --tol 1.2

Đích mặc định là nhạc thấp hơn lời 5 dB (khoảng 4 đến 6 dB) lúc đang nói,
và ở khoảng trống nhạc không thấp hơn lời quá 6 dB để người xem vẫn nghe ra nhạc.
"""
import argparse, os, sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mvlib import SR, read_mono, activity, rms, db, save_json  # noqa: E402

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ap = argparse.ArgumentParser()
ap.add_argument("--target", type=float, default=5.0)
ap.add_argument("--tol", type=float, default=1.2)
a = ap.parse_args()
st = os.path.join(HERE, "audio", "stems")
voice, music = read_mono(os.path.join(st, "voice.wav")), read_mono(os.path.join(st, "music.wav"))
n = min(len(voice), len(music)); voice, music = voice[:n], music[:n]
act = activity(voice, SR) > 0.5
edge = int(0.4 * SR)  # bỏ 0,4 giây quanh mép lời vì bộ duck còn đang chuyển
core = np.convolve(act.astype(float), np.ones(edge) / edge, mode="same") > 0.99
gaps = np.convolve((~act).astype(float), np.ones(edge) / edge, mode="same") > 0.99
gaps[: int(1.0 * SR)] = False; gaps[-int(3.0 * SR):] = False  # bỏ intro và đuôi fade
v = db(rms(voice[core])); ms = db(rms(music[core])); mg = db(rms(music[gaps])) if gaps.any() else float("nan")
under = v - ms
ok = abs(under - a.target) <= a.tol and (np.isnan(mg) or v - mg <= 6.0)
rep = {"voice_db": round(v, 1), "music_speech_db": round(ms, 1), "music_gap_db": round(mg, 1),
       "music_under_voice_db": round(under, 1), "gap_under_voice_db": round(v - mg, 1), "pass": bool(ok)}
save_json(rep, os.path.join(HERE, "audio", "stems", "balance.json"))
print(f"lời {v:.1f} dB | nhạc khi nói {ms:.1f} dB, thấp hơn lời {under:.1f} dB (đích {a.target}±{a.tol})"
      f" | nhạc ở khoảng trống {mg:.1f} dB, thấp hơn lời {v - mg:.1f} dB (đích ≤ 6)")
print("ĐẠT" if ok else "CHƯA ĐẠT, chỉnh audio.balance hoặc audio.gapDb trong script.json rồi chạy lại make_audio.py")
sys.exit(0 if ok else 1)
