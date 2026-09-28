#!/usr/bin/env python3
"""Tải phông từ Google Fonts về thư mục fonts, chỉ lấy 3 bộ ký tự latin, latin-ext và vietnamese,
rồi sinh fonts.css với unicode-range để trình duyệt ghép đủ dấu tiếng Việt khi render không có mạng.

python3 tools/get_fonts.py "Barlow Semi Condensed:600,700,800" "Montserrat:400,500,600,700"
Không truyền gì thì giữ Be Vietnam Pro có sẵn. Cần mạng để tải từ Google Fonts."""
import os, re, sys, urllib.request

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "fonts")
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
FAMILIES = {a.split(":")[0]: [int(w) for w in a.split(":")[1].split(",")] for a in sys.argv[1:]} or {"Be Vietnam Pro": [500, 700, 800]}
os.makedirs(OUT, exist_ok=True)
KEEP = {"latin", "latin-ext", "vietnamese"}


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=30).read()


css_out = []
for fam, weights in FAMILIES.items():
    q = fam.replace(" ", "+") + ":wght@" + ";".join(map(str, weights))
    css = get(f"https://fonts.googleapis.com/css2?family={q}&display=swap").decode()
    for m in re.finditer(r"/\* ([\w-]+) \*/\s*@font-face \{(.*?)\}", css, re.S):
        subset, body = m.group(1), m.group(2)
        if subset not in KEEP:
            continue
        w = re.search(r"font-weight: (\d+)", body).group(1)
        url = re.search(r"url\((.*?)\)", body).group(1)
        rng = re.search(r"unicode-range: (.*?);", body).group(1)
        fn = f"{fam.replace(' ', '')}-{w}-{subset}.woff2"
        path = os.path.join(OUT, fn)
        if not os.path.exists(path):
            open(path, "wb").write(get(url))
        css_out.append(f'@font-face {{ font-family: "{fam}"; font-weight: {w}; font-display: block; '
                       f'src: url("fonts/{fn}") format("woff2"); unicode-range: {rng}; }}')
open(os.path.join(HERE, "fonts.css"), "w").write("\n".join(css_out) + "\n")
print(len(css_out), "khối phông,", len(os.listdir(OUT)), "tệp")
