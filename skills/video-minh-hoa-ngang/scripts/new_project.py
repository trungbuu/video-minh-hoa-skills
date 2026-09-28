#!/usr/bin/env python3
"""Tạo dự án video mới từ template của skill.

python3 scripts/new_project.py <thư mục dự án>
python3 scripts/new_project.py <thư mục dự án> --brand <file brand.css> --logo <logo.png> --mark <dấu.png>

Chép template, chuỗi công cụ vào tools/, vi-type.js và nhật ký project.md.
Thư mục đích phải chưa có hoặc đang trống, để không ghi đè dự án có sẵn.
"""
import argparse, pathlib, re, shutil, sys

SKILL = pathlib.Path(__file__).resolve().parent.parent
IGN = shutil.ignore_patterns(".DS_Store", "__pycache__", "renders", "review", "_cache", ".gitkeep")
ap = argparse.ArgumentParser(description="Tạo dự án video mới")
ap.add_argument("dest")
ap.add_argument("--brand", help="file brand.css của thương hiệu")
ap.add_argument("--logo", help="logo PNG nền trong, dùng ở thẻ kết")
ap.add_argument("--mark", help="dấu logo PNG nền trong, dùng ở đầu khung")
a = ap.parse_args()
dest = pathlib.Path(a.dest).expanduser().resolve()
if dest.exists() and any(dest.iterdir()):
    sys.exit(f"Thư mục {dest} đã có nội dung, hãy chọn thư mục khác.")
shutil.copytree(SKILL / "assets" / "template", dest, dirs_exist_ok=True, ignore=IGN)
(dest / "tools").mkdir(exist_ok=True)
(dest / "audio").mkdir(exist_ok=True)
for f in (SKILL / "assets" / "pipeline").glob("*.py"):
    shutil.copy2(f, dest / "tools" / f.name)
shutil.copy2(SKILL / "assets" / "vi-guard" / "vi-type.js", dest / "vendor" / "vi-type.js")
for opt, name in ((a.brand, "brand.css"), (a.logo, "assets/logo.png"), (a.mark, "assets/mark.png")):
    if opt:
        shutil.copy2(pathlib.Path(opt).expanduser(), dest / name)
slug = re.sub(r"[^a-z0-9-]+", "-", dest.name.lower()).strip("-") or "video"
for meta in ("meta.json", "package.json"):
    p = dest / meta
    p.write_text(re.sub(r'"story"', f'"{slug}"', p.read_text(encoding="utf-8")), encoding="utf-8")
print(f"Đã tạo {dest}")
print("Tiếp theo: viết script.json theo references/kich-ban.md, sửa brand.css nếu cần, rồi chạy")
print(f"  python3 {SKILL / 'scripts' / 'pipeline.py'} {dest} --name {slug}")
