#!/usr/bin/env python3
"""Kiểm script.json trước khi tạo giọng, để bắt lỗi sớm thay vì sau khi render.

python3 scripts/check_script.py <thư mục dự án> [--target 60]

Kiểm các điểm sau và trả mã lỗi 1 nếu có lỗi:
  cấu trúc     có meta, scenes, lines; mỗi dòng trỏ tới cảnh có thật; mỗi cảnh có ít nhất một dòng lời
  kiểu cảnh    thuộc hook, list, point, quiz, stat, cta; trường bắt buộc của từng kiểu
  độ dài chữ   tiêu đề, chip, mục danh sách, đáp án, thẻ kết không vượt giới hạn hiển thị
  lời đọc      mỗi dòng không quá 22 từ; neo {"line", "word"} phải có trong phụ đề của dòng đó
  thời lượng   ước theo 3,5 từ mỗi giây cộng khoảng nghỉ; báo khi lệch quá 15% so với --target
Cảnh báo (không chặn): tiêu đề một từ quá dài, video dưới 3 kiểu cảnh khác nhau.
"""
import argparse, json, pathlib, re, sys, unicodedata

TYPES = {"hook", "list", "point", "quiz", "stat", "cta"}
LIM = {"headline": 34, "kicker": 26, "sub": 44, "chip": 22, "chips": 3, "item": 20, "items": 5, "answer": 30, "cta_row": 28, "words_line": 22}


def fold(s):
    s = unicodedata.normalize("NFD", s.replace("_", " ").lower()).replace("đ", "d")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9 ]+", " ", s).split()


def visible(s):
    return len(re.sub(r"[\[\]_]", "", s or "").replace("\n", " "))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("project"); ap.add_argument("--target", type=float)
    a = ap.parse_args()
    P = pathlib.Path(a.project)
    S = json.loads((P / "script.json").read_text(encoding="utf-8"))
    err, warn = [], []
    for k in ("meta", "scenes", "lines"):
        if k not in S:
            err.append(f"thiếu mục {k}")
    if err:
        print("\n".join("LỖI  " + e for e in err)); sys.exit(1)
    sc, ln = S["scenes"], S["lines"]
    for i, c in enumerate(sc):
        t = c.get("type", "point")
        if t not in TYPES:
            err.append(f"cảnh {i}: kiểu “{t}” không có, chọn một trong {', '.join(sorted(TYPES))}")
        for f in ("headline", "kicker", "sub"):
            if visible(c.get(f)) > LIM[f]:
                err.append(f"cảnh {i}: {f} dài {visible(c.get(f))} ký tự, tối đa {LIM[f]}")
        if len(c.get("chips", [])) > LIM["chips"]:
            err.append(f"cảnh {i}: {len(c['chips'])} chip, tối đa {LIM['chips']}")
        for ch in c.get("chips", []):
            if visible(ch) > LIM["chip"]:
                err.append(f"cảnh {i}: chip “{ch}” dài quá {LIM['chip']} ký tự")
        if t == "list":
            its = c.get("items", [])
            if not 2 <= len(its) <= LIM["items"]:
                err.append(f"cảnh {i}: list cần 2 đến {LIM['items']} mục, đang có {len(its)}")
            for it in its:
                if visible(it[1]) > LIM["item"]:
                    err.append(f"cảnh {i}: mục “{it[1]}” dài quá {LIM['item']} ký tự")
        if t == "quiz" and not (c.get("answer") or {}).get("text"):
            err.append(f"cảnh {i}: quiz cần answer.text")
        if t == "quiz" and visible((c.get("answer") or {}).get("text")) > LIM["answer"]:
            err.append(f"cảnh {i}: đáp án dài quá {LIM['answer']} ký tự")
        if t == "stat" and "value" not in c:
            err.append(f"cảnh {i}: stat cần value")
        if not any(l.get("scene") == i for l in ln):
            err.append(f"cảnh {i}: chưa có dòng lời nào")
        for w in re.sub(r"[\[\]]", "", c.get("headline", "")).split():
            if len(w) > 14:
                warn.append(f"cảnh {i}: từ “{w}” dài, tiêu đề dễ tràn")
    for j, l in enumerate(ln):
        if not 0 <= l.get("scene", -1) < len(sc):
            err.append(f"dòng {j}: scene {l.get('scene')} không tồn tại")
        n = len(l.get("sub", "").replace("_", " ").split())
        if n > LIM["words_line"]:
            err.append(f"dòng {j}: {n} từ, tối đa {LIM['words_line']}, hãy tách thành hai dòng")
    anchors = [(h, "cues") for h in S.get("cues", [])]
    for i, c in enumerate(sc):
        for k in ("countAt", "actionAt", "propAt", "chipsAt", "itemsAt"):
            if isinstance(c.get(k), dict):
                anchors.append((c[k], f"cảnh {i}.{k}"))
        if isinstance((c.get("answer") or {}).get("at"), dict):
            anchors.append((c["answer"]["at"], f"cảnh {i}.answer.at"))
    for h, where in anchors:
        if "word" in h:
            li = h.get("line", -1)
            if not 0 <= li < len(ln):
                err.append(f"{where}: dòng {li} không tồn tại"); continue
            key, toks = fold(h["word"]), fold(ln[li]["sub"])
            if not any(toks[k:k + len(key)] == key for k in range(len(toks))):
                err.append(f"{where}: từ “{h['word']}” không có trong phụ đề dòng {li}")
    cta = S["meta"].get("cta", {})
    for r in cta.get("rows", []):
        if visible(r[0]) + visible(r[1]) > LIM["cta_row"]:
            warn.append(f"thẻ kết: dòng “{r[0]} {r[1]}” dài, có thể xuống dòng")
    kinds = {c.get("type", "point") for c in sc}
    if len(kinds) < 3:
        warn.append(f"chỉ có {len(kinds)} kiểu cảnh, nên dùng ít nhất 3 để đổi nhịp")
    words = sum(len(l.get("sub", "").replace("_", " ").split()) for l in ln)
    est = words / 3.5 + 0.35 * len(ln) + 0.8 * len(sc) + S.get("hold", 2.5)
    est = max(est, sum(c.get("min", 4) for c in sc) + S.get("hold", 2.5))
    msg = f"ước tính {est:.0f} giây ({len(sc)} cảnh, {len(ln)} dòng, {words} từ)"
    if a.target and abs(est - a.target) / a.target > 0.15:
        err.append(msg + f", lệch quá 15% so với đích {a.target:.0f} giây; thêm hoặc bớt cảnh")
    for e in err:
        print("LỖI    " + e)
    for w in warn:
        print("CẢNH BÁO " + w)
    print(("ĐẠT, " if not err else "CHƯA ĐẠT, ") + msg)
    sys.exit(1 if err else 0)


if __name__ == "__main__":
    main()
