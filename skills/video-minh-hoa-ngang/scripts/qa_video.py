#!/usr/bin/env python3
"""Cổng nghiệm thu trước khi bàn giao, bản v2. Báo bằng số đo, không bằng cảm nhận.

python3 scripts/qa_video.py renders/x_giong-doc.mp4 --size 1080x1920 --fps 30 --duration 62.5 --srt renders/x.srt
python3 scripts/qa_video.py renders/x_khong-loi.mp4 --size 1080x1920
python3 scripts/qa_video.py renders/*.mp4 --project .      -> tự lấy thời lượng từ cues.json, đọc thêm cân bằng và self-eval

Mỗi file được kiểm:
  hình, kích thước, fps          có luồng hình, đúng khổ và tốc độ khung
  tiếng                          AAC 48 kHz stereo
  thời lượng                     lệch không quá 0,1 giây
  độ lớn tiếng                   -14 LUFS ± 1 (đổi bằng --lufs, --tol)
  đỉnh thật                      không quá -1 dBTP
  khung đen                      blackdetect không thấy đoạn đen nào ngoài 0,5 giây đầu và cuối
Với --project, kiểm thêm audio/stems/balance.json (nhạc thấp hơn lời 4 đến 6 dB) và review/self-eval.json (0 lỗi),
và file .srt đi kèm nếu truyền --srt. Trả mã lỗi 1 nếu có mục không đạt.
"""
import argparse, json, os, re, subprocess, sys

ap = argparse.ArgumentParser(description="Cổng nghiệm thu video")
ap.add_argument("files", nargs="+")
ap.add_argument("--size", help="ví dụ 1080x1920")
ap.add_argument("--fps", type=float)
ap.add_argument("--duration", type=float)
ap.add_argument("--lufs", type=float, default=-14.0)
ap.add_argument("--tol", type=float, default=1.0)
ap.add_argument("--tp", type=float, default=-1.0)
ap.add_argument("--srt")
ap.add_argument("--project")
ap.add_argument("--silent", action="store_true", help="video không có tiếng, bỏ qua kiểm tra tiếng")
a = ap.parse_args()


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                          "format=duration:stream=codec_type,codec_name,width,height,r_frame_rate,sample_rate,channels",
                          "-of", "json", path], capture_output=True, text=True).stdout
    return json.loads(out or "{}")


def loud(path):
    err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-map", "0:a:0", "-af", "ebur128=peak=true", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    i = re.findall(r"I:\s+(-?[\d.]+) LUFS", err); p = re.findall(r"Peak:\s+(-?[\d.]+|-inf) dBFS", err)
    return (float(i[-1]) if i else None), (float(p[-1]) if p and p[-1] != "-inf" else None)


def black(path, dur):
    err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-vf", "blackdetect=d=0.1:pix_th=0.05", "-an", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    segs = [(float(s), float(e)) for s, e in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", err)]
    return [s for s in segs if s[1] > 0.5 and s[0] < dur - 0.5]


proj = {}
if a.project:
    pr = os.path.abspath(a.project)
    cj = os.path.join(pr, "cues.json")
    if os.path.exists(cj) and a.duration is None:
        a.duration = json.load(open(cj, encoding="utf-8"))["duration"]
    for k, f in (("balance", "audio/stems/balance.json"), ("self_eval", "review/self-eval.json")):
        p = os.path.join(pr, f)
        proj[k] = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None

bad = 0
for f in a.files:
    d = probe(f); ss = d.get("streams", []); dur = float(d.get("format", {}).get("duration", 0))
    v = next((s for s in ss if s["codec_type"] == "video"), None); au = next((s for s in ss if s["codec_type"] == "audio"), None)
    rows = [("hình", v is not None, "có" if v else "thiếu")]
    if v and a.size:
        rows.append(("kích thước", f"{v['width']}x{v['height']}" == a.size, f"{v['width']}x{v['height']}"))
    if v and a.fps:
        n, dd = v["r_frame_rate"].split("/"); fr = float(n) / float(dd)
        rows.append(("fps", abs(fr - a.fps) < 0.01, f"{fr:g}"))
    if a.duration is not None:
        rows.append(("thời lượng", abs(dur - a.duration) <= 0.1, f"{dur:.2f} giây (đích {a.duration})"))
    if not a.silent:
        rows.append(("tiếng", au is not None and au.get("codec_name") == "aac" and au.get("sample_rate") == "48000" and au.get("channels") == 2,
                     f"{au.get('codec_name')} {au.get('sample_rate')} Hz {au.get('channels')} kênh" if au else "thiếu"))
        if au:
            i, p = loud(f)
            rows.append(("độ lớn tiếng", i is not None and abs(i - a.lufs) <= a.tol, f"{i} LUFS (đích {a.lufs}±{a.tol})"))
            rows.append(("đỉnh thật", p is not None and p <= a.tp, f"{p} dBTP (≤ {a.tp})"))
    bl = black(f, dur)
    rows.append(("khung đen", not bl, "không có" if not bl else ", ".join(f"{s:.2f}–{e:.2f}s" for s, e in bl)))
    print(f"\n{f}")
    for name, ok, note in rows:
        print(f"  {'ĐẠT ' if ok else 'LỖI '} {name:<14} {note}")
        bad += 0 if ok else 1

extra = []
if a.srt:
    ok = os.path.exists(a.srt) and os.path.getsize(a.srt) > 0
    extra.append(("phụ đề .srt", ok, a.srt if ok else "thiếu"))
if a.project:
    b = proj.get("balance")
    extra.append(("cân bằng nhạc lời", bool(b and b.get("pass")),
                  f"nhạc thấp hơn lời {b['music_under_voice_db']} dB" if b else "chưa đo, chạy tools/measure_mix.py"))
    s = proj.get("self_eval")
    n = sum(len(x) for x in (s or {}).get("issues", {}).values())
    extra.append(("tự soát DOM", s is not None and n == 0, f"{n} lỗi" if s else "chưa chạy tools/self_eval.py"))
if extra:
    print("\ndự án")
    for name, ok, note in extra:
        print(f"  {'ĐẠT ' if ok else 'LỖI '} {name:<16} {note}")
        bad += 0 if ok else 1
print("\nKẾT QUẢ:", "ĐẠT, được bàn giao" if bad == 0 else f"{bad} mục chưa đạt")
sys.exit(1 if bad else 0)
