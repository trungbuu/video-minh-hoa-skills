#!/usr/bin/env python3
"""Bước 2 của chuỗi v2: căn lời đọc theo từng từ, thay cho cách chia đều 72% câu của bản v1.

python3 tools/align_words.py                  -> audio/voice/lineNN.words.json cho mọi dòng
python3 tools/align_words.py --engine energy  -> ép dùng bộ căn theo năng lượng, không cần model
python3 tools/align_words.py --model small    -> model whisper khác (phải có sẵn trong ~/.cache/whisper)

Hai bộ căn:
  whisper  căn ép buộc (forced alignment). Đưa sẵn câu đã biết vào decoder của whisper rồi dò DTW trên
           ma trận chú ý chéo, nên không phải đoán chữ, chỉ tìm mốc. Chạy máy, dùng model đã tải sẵn,
           mặc định base. Không tự tải model mới vì model nặng hàng trăm MB.
  energy   dự phòng không cần model. Tìm các đoạn có tiếng, bỏ khoảng lặng, rồi trải âm tiết theo độ dài chữ
           trên phần thời gian có tiếng. Khá chính xác với gtts và say vì mỗi dấu phẩy là một khoảng lặng thật.

Mỗi file words.json có:
  spoken   [[âm tiết đọc, bắt đầu, kết thúc], ...] theo câu thật sự được đọc (tts hoặc say)
  display  [[từ phụ đề, bắt đầu, kết thúc], ...] đã khớp về từ hiển thị, “HLV” trải lên “huấn luyện viên”
Mốc tính bằng giây từ đầu file lineNN.wav.
"""
import argparse, json, os, sys, warnings

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mvlib import read_mono, follower, display_words, map_words, save_json  # noqa: E402

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V = os.path.join(HERE, "audio", "voice")


def islands(x, sr, gap=0.09, thresh_db=-38.0):
    """Các đoạn có tiếng [(a, b)] tính bằng giây. Khoảng lặng ngắn hơn gap được nối lại."""
    env = follower(x, sr, 0.005, 0.03)
    ref = max(float(env.max()), 1e-9)
    on = 20 * __import__("numpy").log10(env / ref + 1e-12) > thresh_db
    segs, a = [], None
    for i in range(0, len(on), sr // 200):
        if on[i] and a is None:
            a = i / sr
        if not on[i] and a is not None:
            segs.append([a, i / sr]); a = None
    if a is not None:
        segs.append([a, len(on) / sr])
    merged = []
    for s in segs:
        if merged and s[0] - merged[-1][1] < gap:
            merged[-1][1] = s[1]
        else:
            merged.append(s)
    return [tuple(s) for s in merged if s[1] - s[0] > 0.04] or [(0.0, len(x) / sr)]


def align_energy(wav, text):
    sr = 16000
    x = read_mono(wav, sr)
    toks = [t for t in text.replace("_", " ").split() if t.strip()]
    if not toks:
        return []
    isl = islands(x, sr)
    # thời gian “có tiếng” trải phẳng; mỗi âm tiết nặng theo số chữ cái, dấu câu cuối tăng nhẹ vì kéo dài
    wts = [max(2, len(t.strip(",.!?;:"))) + (1.5 if t[-1] in ",.!?;:" else 0) for t in toks]
    total_voiced = sum(b - a for a, b in isl)
    # nếu số khoảng lặng lớn trùng số dấu câu, gán từng cụm vào từng đảo tiếng cho chính xác hơn
    groups, cur = [], []
    for t in toks:
        cur.append(t)
        if t[-1] in ",.!?;:":
            groups.append(cur); cur = []
    if cur:
        groups.append(cur)
    out = []
    if len(groups) == len(isl) and len(isl) > 1:
        k = 0
        for g, (a, b) in zip(groups, isl):
            gw = wts[k:k + len(g)]; tot = sum(gw); acc = 0
            for t, w in zip(g, gw):
                out.append([t, round(a + (b - a) * acc / tot, 3), round(a + (b - a) * (acc + w) / tot, 3)]); acc += w
            k += len(g)
        return out
    tot, acc = sum(wts), 0.0

    def at(u):  # u là tỉ lệ 0..1 trên thời gian có tiếng -> giây thật
        need = u * total_voiced
        for a, b in isl:
            if need <= b - a:
                return a + need
            need -= b - a
        return isl[-1][1]
    for t, w in zip(toks, wts):
        out.append([t, round(at(acc / tot), 3), round(at((acc + w) / tot), 3)]); acc += w
    return out


_model = None


def align_whisper(wav, text, model_name):
    global _model
    import torch, whisper
    from whisper.timing import find_alignment
    from whisper.tokenizer import get_tokenizer
    path = os.path.expanduser(f"~/.cache/whisper/{model_name}.pt")
    if not os.path.exists(path):
        raise FileNotFoundError(f"chưa có model {model_name} trong ~/.cache/whisper, không tự tải")
    if _model is None:
        _model = whisper.load_model(model_name, device="cpu")
    tok = get_tokenizer(_model.is_multilingual, language="vi", task="transcribe")
    audio = whisper.load_audio(wav)
    mel = whisper.log_mel_spectrogram(audio, _model.dims.n_mels)
    nframes = mel.shape[-1]
    if nframes > whisper.audio.N_FRAMES:
        raise ValueError("dòng dài hơn 30 giây, hãy tách dòng")
    mel = whisper.pad_or_trim(mel, whisper.audio.N_FRAMES)
    words = [w for w in text.replace("_", " ").split() if w.strip()]
    ids = tok.encode(" " + " ".join(words))
    with torch.no_grad():
        timing = find_alignment(_model, tok, ids, mel, nframes)
    out = [[w.word.strip(), round(float(w.start), 3), round(float(w.end), 3)] for w in timing if w.word.strip()]
    # kẹp vào vùng có tiếng để mốc đầu không rơi vào khoảng lặng đầu file
    sr = 16000
    isl = islands(read_mono(wav, sr), sr)
    a0, b0 = isl[0][0], isl[-1][1]
    for w in out:
        w[1] = round(min(max(w[1], a0), b0), 3); w[2] = round(min(max(w[2], w[1]), b0), 3)
    if len(out) < max(1, len(words) // 2):
        raise ValueError("căn được quá ít từ")
    return out


def main():
    ap = argparse.ArgumentParser(description="Căn lời đọc theo từng từ")
    ap.add_argument("--engine", choices=["auto", "whisper", "energy"], default="auto")
    ap.add_argument("--model", default="base")
    a = ap.parse_args()
    S = json.load(open(os.path.join(HERE, "script.json"), encoding="utf-8"))
    VJ = json.load(open(os.path.join(V, "voice.json"), encoding="utf-8"))
    used = set()
    for m in VJ["lines"]:
        i = m["i"]; wav = os.path.join(HERE, m["file"]); spoken_text = m["spoken"]
        eng = a.engine
        spoken = None
        if eng in ("auto", "whisper"):
            try:
                spoken = align_whisper(wav, spoken_text, a.model); eng = "whisper"
            except Exception as e:  # noqa: BLE001
                if a.engine == "whisper":
                    sys.exit(f"line{i:02d}: {e}")
                print(f"  line{i:02d}: whisper không dùng được ({e}), chuyển sang energy")
        if spoken is None:
            spoken = align_energy(wav, spoken_text); eng = "energy"
        used.add(eng)
        disp = map_words(display_words(S["lines"][i]["sub"]), [tuple(w) for w in spoken])
        save_json({"engine": eng, "spoken": spoken, "display": [list(w) for w in disp]}, os.path.join(V, f"line{i:02d}.words.json"))
        print(f"  line{i:02d} [{eng}] " + " ".join(f"{w}@{s:.2f}" for w, s, _ in disp))
    print("bộ căn đã dùng:", ", ".join(sorted(used)))


if __name__ == "__main__":
    main()
