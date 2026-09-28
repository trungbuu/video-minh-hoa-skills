"""Thư viện dùng chung cho chuỗi dựng video v2 của motion-video-vi.

Gồm đọc ghi âm thanh qua ffmpeg, đo độ lớn tiếng EBU R128, đường bao kiểu sidechain,
master về -14 LUFS với đỉnh thật từ -1,5 dBTP trở xuống, chuẩn hoá chữ để so khớp lời
và bộ giải neo cue theo từ, theo phách, theo giây.

Chỉ cần numpy và ffmpeg. Không dùng scipy hay librosa để chạy được trên máy trắng.
"""
from __future__ import annotations

import json
import math
import os
import re
import subprocess
import unicodedata
from difflib import SequenceMatcher

import numpy as np

SR = 48000
TARGET_LUFS = -14.0
TARGET_TP = -1.5


# ---------------------------------------------------------------- ffmpeg
def ff(*args: str) -> None:
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)


def duration(path: str) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                         capture_output=True, text=True).stdout.strip()
    return float(out or 0)


def read_mono(path: str, sr: int = SR) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(sr), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype="<f4").astype(np.float64)


def write_wav(sig: np.ndarray, path: str, sr: int = SR, stereo: bool = True) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    raw = path + ".f32"
    np.asarray(sig, dtype="<f4").tofile(raw)
    ff("-f", "f32le", "-ar", str(sr), "-ac", "1", "-i", raw, "-ac", "2" if stereo else "1", "-c:a", "pcm_s24le", path)
    os.remove(raw)


def measure(path: str) -> tuple[float, float]:
    """Trả về (LUFS tích hợp, đỉnh thật dBTP) của luồng tiếng đầu tiên."""
    err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-map", "0:a:0", "-af", "ebur128=peak=true",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    i = re.findall(r"I:\s+(-?[\d.]+|-inf) LUFS", err)
    p = re.findall(r"Peak:\s+(-?[\d.]+|-inf) dBFS", err)
    lufs = float(i[-1]) if i and i[-1] != "-inf" else -70.0
    tp = float(p[-1]) if p and p[-1] != "-inf" else -70.0
    return lufs, tp


def db(x: float) -> float:
    return 20 * math.log10(max(x, 1e-12))


def rms(x: np.ndarray) -> float:
    return float(np.sqrt(np.mean(x ** 2))) if len(x) else 0.0


# ---------------------------------------------------------------- master
def master(sig: np.ndarray, path: str, lufs: float = TARGET_LUFS, tp: float = TARGET_TP, sr: int = SR) -> tuple[float, float]:
    """Master tín hiệu mono về mức đích. Chặn đỉnh ở 192 kHz (lấy mẫu dư 4 lần) nên đỉnh thật bám sát giới hạn.
    Lặp tối đa 6 lần để bù phần tiếng mà bộ chặn đỉnh ăn mất. Trả về (LUFS, dBTP) đo được."""
    peak = float(np.max(np.abs(sig))) or 1.0
    tmp = path + ".pre.wav"
    write_wav(sig * (0.5 / peak), tmp, sr)
    gain = lufs - measure(tmp)[0]
    limit = 10 ** ((tp - 0.3) / 20)
    got = (0.0, 0.0)
    for _ in range(6):
        ff("-i", tmp, "-af", f"aresample=192000,volume={gain:.3f}dB,alimiter=limit={limit:.4f}:level=0:attack=1:release=60,"
           f"aresample={sr}", "-ar", str(sr), "-ac", "2", "-c:a", "pcm_s24le", path)
        got = measure(path)
        if abs(got[0] - lufs) < 0.25:
            break
        gain += lufs - got[0]
    os.remove(tmp)
    return got


# ---------------------------------------------------------------- đường bao
def follower(x: np.ndarray, sr: int, attack: float = 0.015, release: float = 0.35, rate: int = 1000) -> np.ndarray:
    """Đường bao biên độ kiểu bộ nén sidechain: lên nhanh theo attack, xuống chậm theo release.
    Tính ở tốc độ rate mẫu mỗi giây rồi nội suy lại, nên nhanh dù dùng vòng lặp Python."""
    hop = max(1, sr // rate)
    n = len(x) // hop
    if n == 0:
        return np.zeros_like(x)
    blk = np.sqrt(np.mean(x[: n * hop].reshape(n, hop) ** 2, axis=1))
    a_up = 1 - math.exp(-1 / (attack * rate))
    a_dn = 1 - math.exp(-1 / (release * rate))
    env = np.empty(n)
    y = 0.0
    for i, v in enumerate(blk):
        y += (a_up if v > y else a_dn) * (v - y)
        env[i] = y
    return np.interp(np.arange(len(x)), np.arange(n) * hop + hop / 2, env)


def activity(voice: np.ndarray, sr: int, thresh_db: float = -45.0) -> np.ndarray:
    """Mặt nạ 0..1 cho biết lúc nào đang có lời, dùng để đo cân bằng và điều khiển ducking."""
    env = follower(voice, sr, 0.01, 0.25)
    ref = np.max(env) or 1.0
    return (20 * np.log10(np.maximum(env / ref, 1e-9)) > thresh_db).astype(float)


def frame_envelope(voice: np.ndarray, sr: int, fps: int = 30) -> list[float]:
    """Đường bao lời đọc theo từng khung hình, chuẩn hoá 0..1, để cảnh cho nhân vật nói hay sóng âm nảy."""
    env = follower(voice, sr, 0.01, 0.12)
    hop = sr / fps
    n = int(len(voice) / hop)
    vals = [float(env[min(len(env) - 1, int((k + 0.5) * hop))]) for k in range(n)]
    top = np.percentile(vals, 98) if vals else 1.0
    return [round(min(1.0, v / (top or 1.0)), 3) for v in vals]


# ---------------------------------------------------------------- chữ
NB = "\u00a0"


def fold(s: str) -> str:
    """Chữ thường, bỏ dấu câu, giữ dấu tiếng Việt. Dùng để so khớp từ phụ đề với từ được đọc."""
    s = s.replace("_", " ").replace(NB, " ").lower()
    s = re.sub(r"[“”\"'‘’.,!?;:()\[\]…–—\-/]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def ascii_fold(s: str) -> str:
    s = unicodedata.normalize("NFD", fold(s)).replace("đ", "d")
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def display_words(sub: str) -> list[str]:
    """Từ hiển thị của phụ đề. Dấu “_” nối âm tiết của một từ ghép thành một từ karaoke."""
    return [w for w in sub.split(" ") if w.strip()]


def map_words(display: list[str], spoken: list[tuple[str, float, float]]) -> list[tuple[str, float, float]]:
    """Gán mốc cho từng từ hiển thị từ danh sách âm tiết đã căn (spoken).
    So khớp theo âm tiết đã bỏ dấu. Khối thay thế như “HLV” với “huấn luyện viên” được trải đều theo độ dài."""
    if not spoken:
        return [(w, 0.0, 0.0) for w in display]
    syl, owner = [], []
    for k, w in enumerate(display):
        parts = ascii_fold(w).split() or [ascii_fold(w) or "_"]
        for p in parts:
            syl.append(p)
            owner.append(k)
    sp = [ascii_fold(w).replace(" ", "") or "_" for w, _, _ in spoken]
    times: list[tuple[float, float] | None] = [None] * len(syl)
    sm = SequenceMatcher(a=syl, b=sp, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for d in range(i2 - i1):
                times[i1 + d] = (spoken[j1 + d][1], spoken[j1 + d][2])
        elif tag == "replace" or (tag == "delete" and j1 == j2):
            if j2 > j1:
                a, b = spoken[j1][1], spoken[j2 - 1][2]
            else:  # từ không được đọc: kẹp giữa hai âm tiết kề bên
                a = spoken[j1 - 1][2] if j1 > 0 else spoken[0][1]
                b = spoken[j1][1] if j1 < len(spoken) else spoken[-1][2]
            wts = [max(1, len(syl[i])) for i in range(i1, i2)]
            tot, acc = sum(wts), 0
            for i, wt in zip(range(i1, i2), wts):
                times[i] = (a + (b - a) * acc / tot, a + (b - a) * (acc + wt) / tot)
                acc += wt
    # lấp chỗ trống còn lại bằng nội suy tuyến tính
    for i, tv in enumerate(times):
        if tv is None:
            prev = next((times[j][1] for j in range(i - 1, -1, -1) if times[j]), spoken[0][1])
            nxt = next((times[j][0] for j in range(i + 1, len(times)) if times[j]), spoken[-1][2])
            times[i] = (prev, max(prev, nxt))
    out = []
    for k, w in enumerate(display):
        ts = [times[i] for i in range(len(syl)) if owner[i] == k]
        out.append((w, round(min(t[0] for t in ts), 3), round(max(t[1] for t in ts), 3)))
    for k in range(1, len(out)):  # bảo đảm tăng dần
        if out[k][1] < out[k - 1][1]:
            out[k] = (out[k][0], out[k - 1][1], max(out[k - 1][1], out[k][2]))
    return out


# ---------------------------------------------------------------- neo cue
def syl_match(key: list[str], toks: list[str]) -> bool:
    """key là dãy âm tiết liền nhau nằm trong toks. So nguyên âm tiết nên “ba” không khớp nhầm “bạn”."""
    n = len(key)
    return any(toks[i:i + n] == key for i in range(len(toks) - n + 1))


def resolve_anchor(h: dict, ctx: dict) -> float | None:
    """Giải một neo thành giây tuyệt đối. Mỗi neo dùng đúng một kiểu:
    {"line": i, "word": "từ", "nth": 1}  lúc từ đó bắt đầu được đọc (nth đếm từ 1)
    {"scene": k, "at": 0.4}              0,4 giây sau điểm cắt cảnh k
    {"beat": n}                          phách thứ n của lưới nhạc
    {"abs": 12.3}                        giây tuyệt đối
    Thêm "offset" để dời sớm hoặc muộn, ví dụ -0.05 để tiếng rơi trước khung va chạm."""
    off = float(h.get("offset", 0))
    if "word" in h:
        words = ctx["words"].get(int(h["line"]), [])
        key, nth, seen = ascii_fold(h["word"]).split(), int(h.get("nth", 1)), 0
        for w, s, _e in words:
            if key and syl_match(key, ascii_fold(w).split()):
                seen += 1
                if seen == nth:
                    return round(s + off, 3)
        return None
    if "at" in h and "scene" in h:
        return round(ctx["scenes"][int(h["scene"])] + float(h["at"]) + off, 3)
    if "beat" in h:
        return round(ctx["beat0"] + float(h["beat"]) * 60 / ctx["bpm"] + off, 3)
    if "abs" in h:
        return round(float(h["abs"]) + off, 3)
    return None


def load_json(path: str, default=None):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(obj, path: str, indent: int | None = 1) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent)
