#!/usr/bin/env python3
"""Bước 3 của chuỗi v2: xếp lời vào cảnh theo lưới phách, giải neo cue, chia cụm phụ đề. Ghi cues.json.

python3 tools/layout.py
python3 tools/layout.py --dry      -> chỉ in lịch, không ghi file

Đọc script.json, audio/voice/voice.json và audio/voice/lineNN.words.json.
Mỗi cảnh dài vừa đủ cho lời của nó (tối thiểu minScene[k]) rồi làm tròn lên phách kế tiếp,
nên điểm cắt cảnh luôn rơi đúng phách. Phụ đề mang mốc từng từ thật, không còn chia đều.

Neo cue trong script.json, mục "cues", mỗi mục một kiểu neo:
  {"line": 2, "word": "Alignment", "sfx": "pop"}      lúc từ “Alignment” của dòng 2 bắt đầu được đọc
  {"scene": 3, "at": 0.5, "sfx": "whoosh"}             0,5 giây sau điểm cắt cảnh 3
  {"beat": 32, "sfx": "boom", "vol": 0.6}               phách 32
  {"abs": 12.0, "sfx": "ding"}                          giây tuyệt đối
Thêm "offset" để dời, "hit": false nếu chỉ có tiếng mà không cần hình nảy theo.
Sửa lời đọc thì các mốc theo từ tự dời theo, không phải sửa tay.
"""
import argparse, json, math, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mvlib import resolve_anchor, save_json, load_json  # noqa: E402

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def chunk(words, maxw=9):
    """Chia một dòng dài thành ít cụm nhất có thể (mỗi cụm tối đa maxw từ), các cụm dài gần bằng nhau.
    Điểm ngắt ưu tiên ngay sau dấu câu nếu nằm trong khoảng 3 từ quanh điểm chia đều."""
    n = len(words)
    parts = -(-n // maxw)
    if parts <= 1:
        return [words]
    cuts, prev = [], 0
    for p in range(1, parts):
        ideal = round(n * p / parts)
        cands = [k for k in range(max(prev + 2, ideal - 3), min(n - 1, ideal + 3) + 1)]
        best = min(cands, key=lambda k: abs(k - ideal) - (2.5 if words[k - 1][0][-1:] in ",.;:!?”" else 0)) if cands else ideal
        cuts.append(best); prev = best
    bounds = [0, *cuts, n]
    return [words[bounds[i]:bounds[i + 1]] for i in range(len(bounds) - 1)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    S = json.load(open(os.path.join(HERE, "script.json"), encoding="utf-8"))
    VJ = json.load(open(os.path.join(HERE, "audio", "voice", "voice.json"), encoding="utf-8"))
    bpm = S.get("bpm", 120); beat0 = S.get("beat0", 0.0); BEAT = 60 / bpm
    lead, gap, tail = S.get("lead", 0.35), S.get("gap", 0.28), S.get("tail", 0.5)
    mins = S.get("minScene") or [sc.get("min", 4.0) for sc in S["scenes"]]; nsc = len(mins)
    dur = {m["i"]: m["dur"] for m in VJ["lines"]}
    words = {}
    for i in range(len(S["lines"])):
        wj = load_json(os.path.join(HERE, "audio", "voice", f"line{i:02d}.words.json"))
        words[i] = wj["display"] if wj else []

    scenes, place, t = [], {}, beat0
    for sc in range(nsc):
        scenes.append(round(t, 3))
        cur = t + lead
        for i, ln in enumerate(S["lines"]):
            if ln["scene"] != sc:
                continue
            place[i] = round(cur, 3)
            cur += dur[i] + ln.get("pause", gap)
        end = max(t + mins[sc], cur - gap + tail)
        t = beat0 + math.ceil((end - beat0) / BEAT - 1e-6) * BEAT
    total = round(t + S.get("hold", 2.0), 3)
    ending = scenes[-1]

    absw = {i: [[w, round(place[i] + s, 3), round(place[i] + e, 3)] for w, s, e in words[i]] for i in place}
    caps = []
    order = sorted(place, key=lambda i: place[i])
    for i in order:
        ws = absw[i] or [[x, place[i], place[i] + dur[i]] for x in S["lines"][i]["sub"].split()]
        for part in chunk(ws, S.get("capMaxWords", 9)):
            caps.append({"line": i, "sc": S["lines"][i]["scene"], "v": part[0][1], "w": part,
                         "s": " ".join(w for w, _, _ in part)})
    for k, c in enumerate(caps):
        same = k + 1 < len(caps) and caps[k + 1]["sc"] == c["sc"]
        nxt = caps[k + 1]["v"] - 0.06 if same else (scenes[c["sc"] + 1] if c["sc"] + 1 < nsc else total + 0.1)
        c["a"], c["b"] = round(max(scenes[c["sc"]], c["v"] - 0.15), 3), round(nxt, 3)

    ctx = {"words": absw, "scenes": scenes, "beat0": beat0, "bpm": bpm}
    sfx, missing = [], []
    auto = S.get("autoSfx", {"sceneCut": "whoosh", "ending": "chime"})
    if auto.get("sceneCut"):
        sfx += [{"t": round(s - 0.3, 3), "sfx": auto["sceneCut"], "vol": 0.35, "hit": False} for s in scenes[1:]]
    if auto.get("ending"):
        sfx.append({"t": ending, "sfx": auto["ending"], "vol": 0.4, "hit": False})
    for h in S.get("cues", []):
        tt = resolve_anchor(h, ctx)
        if tt is None:
            missing.append(h); continue
        sfx.append({"t": tt, "sfx": h.get("sfx", "pop"), "vol": h.get("vol", 0.5), "hit": h.get("hit", True),
                    "id": h.get("id", "")})
    sfx.sort(key=lambda x: x["t"])

    cues = {
        "_ghichu": f"Tự sinh bởi tools/layout.py, máy đọc {VJ['engine']}. Không sửa tay, sửa script.json rồi chạy lại.",
        "duration": total, "bpm": bpm, "beat0": beat0, "scenes": scenes, "ending": ending, "engine": VJ["engine"],
        "voice": [{"file": f"audio/voice/line{i:02d}.wav", "at": place[i], "line": i} for i in order],
        "lines": [{"i": i, "sc": S["lines"][i]["scene"], "v": place[i], "d": dur[i]} for i in order],
        "words": {str(i): absw[i] for i in order},
        "caps": caps,
        "sfx": sfx,
        "hits": [x["t"] for x in sfx if x.get("hit")],
        "ids": {x["id"]: x["t"] for x in sfx if x.get("id")},
    }
    print(f"cảnh (giây): {scenes}  tổng {total} giây, {len(caps)} cụm phụ đề, {len(sfx)} SFX")
    for i in order:
        print(f"  {place[i]:6.2f}s  cảnh {S['lines'][i]['scene']}  {S['lines'][i]['sub'].replace('_', ' ')}")
    for h in missing:
        print("  CẢNH BÁO neo không tìm thấy:", json.dumps(h, ensure_ascii=False))
    over = [c for c in caps if c["w"] and c["w"][-1][1] > c["b"] - 0.1]
    for c in over:
        print(f"  CẢNH BÁO từ cuối của cụm bắt đầu sau khi cụm đã tắt: {c['s']}")
    late = [(i, place[i] + dur[i]) for i in order
            if S["lines"][i]["scene"] + 1 < nsc and place[i] + dur[i] > scenes[S["lines"][i]["scene"] + 1] - 0.1]
    for i, e in late:
        print(f"  CẢNH BÁO lời dòng {i} chạy tới {e:.2f}s, lấn sang cảnh sau")
    if not a.dry:
        save_json(cues, os.path.join(HERE, "cues.json"))
    if missing:
        sys.exit(1)


if __name__ == "__main__":
    main()
