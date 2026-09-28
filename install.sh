#!/usr/bin/env bash
# Chép hai skill vào thư mục skill cá nhân của Claude Code. Chạy lại để cập nhật.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
dest="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
mkdir -p "$dest"
for s in video-minh-hoa-doc video-minh-hoa-ngang; do
  rm -rf "$dest/$s"
  cp -R "$here/skills/$s" "$dest/$s"
  echo "đã cài $s vào $dest/$s"
done
for c in node ffmpeg ffprobe python3; do
  command -v "$c" >/dev/null || echo "cảnh báo: chưa có $c trên máy"
done
python3 -c "import numpy, PIL, playwright" 2>/dev/null || echo "cảnh báo: thiếu gói Python, chạy: pip install numpy pillow playwright"
python3 -c "import gtts" 2>/dev/null || echo "gợi ý: pip install gTTS để có giọng đọc tiếng Việt"
python3 -c "import whisper" 2>/dev/null || echo "gợi ý: pip install openai-whisper để căn lời chính xác hơn"
echo "xong. Mở Claude Code và gõ: làm video dọc minh hoạ tài liệu <tên file>"
