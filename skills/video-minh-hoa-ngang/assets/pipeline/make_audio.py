#!/usr/bin/env python3
"""Bước 4 của chuỗi v2: nhạc, SFX, lời đọc, ducking kiểu sidechain và master. Đọc cues.json.

python3 tools/make_audio.py

Đầu ra gồm có:
  audio/mix.wav        bản có lời, -14 LUFS, đỉnh thật từ -1,5 dBTP trở xuống
  audio/bed.wav        bản không lời (nhạc và SFX) cho Reels tắt tiếng, cùng chuẩn
  audio/music.wav      stem nhạc gốc để hyperframes beats đo phách
  audio/stems/*.wav    nhạc đã duck, lời, SFX ở cùng thang để tools/measure_mix.py đo cân bằng
  audio/vo-env.json    đường bao lời theo khung hình, cảnh dùng để cho nhân vật nói

Thiết lập trong script.json, mục "audio" (đều tuỳ chọn):
  music       đường dẫn nhạc thật; bỏ trống thì tổng hợp bản giữ chỗ theo bpm
  balance     nhạc thấp hơn lời bao nhiêu dB khi đang nói, mặc định 5 (đích 4 đến 6)
  gapDb       nhạc thấp hơn lời bao nhiêu dB ở khoảng trống, mặc định 2
  attack, release   thời gian của bộ duck, mặc định 0,015 và 0,35 giây
  sfxDb       SFX thấp hơn lời bao nhiêu dB ở vol 0,5, mặc định 8
Thiết kế lấy từ motion-video (bestagentkits): bản đầu của họ duck quá sâu, người xem kêu “không có nhạc”.
"""
import os, sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mvlib import (SR, TARGET_LUFS, TARGET_TP, read_mono, write_wav, master, follower, activity,  # noqa: E402
                   frame_envelope, rms, db, load_json, save_json)

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(HERE, "audio")
S = load_json(os.path.join(HERE, "script.json"), {})
C = load_json(os.path.join(HERE, "cues.json"))
CFG = {"balance": 5.0, "gapDb": 2.0, "attack": 0.015, "release": 0.35, "sfxDb": 8.0, **S.get("audio", {})}
DUR, BPM = C["duration"], C["bpm"]
N = int(SR * DUR)
rng = np.random.default_rng(7)
beat = 60 / BPM


def env(n, attack, decay):
    x = np.arange(n) / SR
    return np.minimum(1, x / max(attack, 1e-4)) * np.exp(-x / decay)


def place(buf, sig, at, gain=1.0):
    i = int(at * SR); j = min(len(buf), i + len(sig))
    if 0 <= i < len(buf):
        buf[i:j] += gain * sig[: j - i]


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def saw(f, x, k=6):
    return sum(np.sin(2 * np.pi * f * h * x) / h for h in range(1, k + 1))


def synth_music():
    """Nhạc giữ chỗ năng lượng vừa: pad, bass nảy nửa phách, pluck rải nốt, kick mỗi phách từ phách 5."""
    music = np.zeros(N)
    bar = 4 * beat
    prog = [[57, 60, 64, 69], [53, 57, 60, 65], [48, 55, 60, 64], [55, 59, 62, 67]]
    roots = [45, 41, 48, 43]
    b0 = C.get("beat0", 0.0)
    for k in range(int(np.ceil(DUR / bar))):
        t0 = b0 + k * bar; ch = prog[k % 4]
        n = int((bar + 0.6) * SR); x = np.arange(n) / SR
        shape = np.minimum(1, x / 0.25) * np.clip((bar + 0.6 - x) / 0.6, 0, 1)
        for j, m in enumerate(ch):
            place(music, saw(hz(m), x, 4) * shape * (1 + 0.1 * np.sin(2 * np.pi * 0.5 * x + j)), t0, 0.022)
        for s in range(8):
            n = int(0.24 * SR); x = np.arange(n) / SR
            f = hz(roots[k % 4] - 12 + (12 if s % 4 == 3 else 0))
            place(music, np.tanh(2.2 * np.sin(2 * np.pi * f * x)) * env(n, 0.004, 0.14), t0 + s * beat / 2, 0.16 if s % 2 == 0 else 0.1)
        arp = [ch[0], ch[1], ch[2], ch[3], ch[2], ch[1], ch[3], ch[2]]
        for s in range(8):
            n = int(0.5 * SR); x = np.arange(n) / SR; f = hz(arp[s] + 12)
            place(music, (np.sin(2 * np.pi * f * x) + 0.3 * np.sin(4 * np.pi * f * x)) * env(n, 0.002, 0.13), t0 + s * beat / 2, 0.07)
    end_fade = DUR - 0.2
    for k in range(int(DUR / beat) + 1):
        at = b0 + k * beat
        if at > end_fade:
            break
        if k >= 4:
            n = int(0.3 * SR); x = np.arange(n) / SR
            f = 48 + 110 * np.exp(-x / 0.03)
            place(music, np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.002, 0.12), at, 0.55 if k % 4 == 0 else 0.42)
        if k % 2 == 1 and k >= 4:
            n = int(0.18 * SR); noise = np.diff(rng.standard_normal(n), prepend=0)
            place(music, noise * env(n, 0.001, 0.05), at, 0.09)
        for h in (0, 0.5):
            n = int(0.05 * SR); noise = np.diff(np.diff(rng.standard_normal(n), prepend=0), prepend=0)
            place(music, noise * env(n, 0.0005, 0.012), at + h * beat, 0.02 if h else 0.012)
    return music


def load_music(path):
    x = read_mono(os.path.join(HERE, path))
    if len(x) < N:
        x = np.tile(x, int(np.ceil(N / len(x))))
    return x[:N]


# ---------- thư viện SFX tổng hợp, không cần file ngoài ----------
def sfx_whoosh(d=0.45):
    n = int(d * SR); x = np.arange(n) / SR; noise = rng.standard_normal(n)
    out = np.zeros(n); y = 0.0
    a = 1 - np.exp(-2 * np.pi * (400 + 5000 * np.sin(np.pi * x / d) ** 2) / SR)
    for i in range(n):
        y += a[i] * (noise[i] - y); out[i] = y
    return out * np.sin(np.pi * x / d) ** 1.5


def sfx_pop():
    n = int(0.18 * SR); x = np.arange(n) / SR
    return np.sin(2 * np.pi * np.cumsum(900 * np.exp(-x / 0.03) + 300) / SR) * env(n, 0.001, 0.05)


def sfx_ding():
    n = int(1.0 * SR); x = np.arange(n) / SR
    return (np.sin(2 * np.pi * hz(88) * x) + 0.4 * np.sin(2 * np.pi * hz(95) * x)) * env(n, 0.002, 0.28)


def sfx_chime():
    out = np.zeros(int(1.9 * SR))
    for i, m in enumerate([76, 81, 84, 88]):
        n = int(1.4 * SR); x = np.arange(n) / SR
        place(out, np.sin(2 * np.pi * hz(m) * x) * env(n, 0.002, 0.4), i * beat / 4)
    return out


def sfx_boom():
    n = int(0.9 * SR); x = np.arange(n) / SR
    body = np.sin(2 * np.pi * np.cumsum(40 + 90 * np.exp(-x / 0.05)) / SR) * env(n, 0.002, 0.35)
    return body + 0.3 * rng.standard_normal(n) * env(n, 0.001, 0.04)


def sfx_tick():
    n = int(0.06 * SR); x = np.arange(n) / SR
    return np.sin(2 * np.pi * 2200 * x) * env(n, 0.0005, 0.012)


def sfx_rise(d=0.8):
    n = int(d * SR); x = np.arange(n) / SR
    return np.sin(2 * np.pi * np.cumsum(300 + 1500 * (x / d) ** 2) / SR) * (x / d) ** 2 * 0.6


LIB = {"whoosh": sfx_whoosh(), "pop": sfx_pop(), "ding": sfx_ding(), "chime": sfx_chime(), "boom": sfx_boom(),
       "tick": sfx_tick(), "rise": sfx_rise()}
ATTACK = {"rise": 0.8}  # SFX có đoạn dẫn thì bắt đầu sớm để đỉnh rơi đúng mốc


def main():
    music = load_music(CFG["music"]) if CFG.get("music") else synth_music()
    fade = int(2.5 * SR); music[-fade:] *= np.linspace(1, 0, fade)
    music[: int(0.3 * SR)] *= np.linspace(0, 1, int(0.3 * SR))

    voice = np.zeros(N)
    for v in C.get("voice", []):
        place(voice, read_mono(os.path.join(HERE, v["file"])), v["at"])
    has_voice = bool(np.any(np.abs(voice) > 1e-4))
    act = activity(voice, SR) if has_voice else np.zeros(N)
    v_db = db(rms(voice[act > 0.5])) if has_voice else db(rms(music)) + 2
    m_db = db(rms(music[music != 0]))
    g_gap = 10 ** ((v_db - CFG["gapDb"] - m_db) / 20)
    g_sp = 10 ** ((v_db - CFG["balance"] - m_db) / 20)
    drive = np.clip(follower(act, SR, CFG["attack"], CFG["release"]) * 1.25, 0, 1) if has_voice else np.zeros(N)
    music_d = music * (g_gap + (g_sp - g_gap) * drive)

    sfx = np.zeros(N)
    ref = 10 ** ((v_db - CFG["sfxDb"]) / 20)
    for h in C.get("sfx", []):
        s = LIB.get(h["sfx"])
        if s is None:
            print("  bỏ qua SFX chưa có trong thư viện:", h["sfx"]); continue
        k = ref / max(rms(s[np.abs(s) > 1e-3]), 1e-9) * (h.get("vol", 0.5) / 0.5)
        place(sfx, s, h["t"] - ATTACK.get(h["sfx"], 0), k)

    os.makedirs(os.path.join(A, "stems"), exist_ok=True)
    mix = music_d + sfx + voice
    lufs, tp = master(mix, os.path.join(A, "mix.wav"), TARGET_LUFS, TARGET_TP)
    blufs, btp = master(music * g_gap + sfx, os.path.join(A, "bed.wav"), TARGET_LUFS, TARGET_TP)
    sc = 0.5 / max(np.max(np.abs(mix)), 1e-9)
    write_wav(music * 0.5 / max(np.max(np.abs(music)), 1e-9), os.path.join(A, "music.wav"))
    for name, sig in (("music", music_d), ("voice", voice), ("sfx", sfx)):
        write_wav(sig * sc, os.path.join(A, "stems", name + ".wav"))
    save_json({"fps": 30, "env": frame_envelope(voice, SR, 30) if has_voice else []}, os.path.join(A, "vo-env.json"), None)
    print(f"audio/mix.wav  {lufs:.1f} LUFS, đỉnh thật {tp:.1f} dBTP, {DUR} giây")
    print(f"audio/bed.wav  {blufs:.1f} LUFS, đỉnh thật {btp:.1f} dBTP (bản không lời)")
    print(f"duck: nhạc thấp hơn lời {CFG['balance']} dB khi nói, {CFG['gapDb']} dB ở khoảng trống. Đo lại bằng tools/measure_mix.py")


if __name__ == "__main__":
    main()
