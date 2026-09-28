#!/usr/bin/env bash
# Cài hai skill cho Claude Code (mặc định) hoặc Codex. Chạy lại để cập nhật.
#   ./install.sh          -> ~/.claude/skills
#   ./install.sh codex    -> ~/.agents/skills (Codex)
#   ./install.sh all      -> cả hai
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
case "${1:-claude}" in
  claude) targets=("${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}") ;;
  codex)  targets=("$HOME/.agents/skills") ;;
  all)    targets=("${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}" "$HOME/.agents/skills") ;;
  *) echo "dùng: ./install.sh [claude|codex|all]"; exit 1 ;;
esac
for dest in "${targets[@]}"; do
  mkdir -p "$dest"
  for s in video-minh-hoa-doc video-minh-hoa-ngang; do
    rm -rf "$dest/$s"; cp -R "$here/skills/$s" "$dest/$s"
    echo "đã cài $s vào $dest/$s"
  done
done
for c in node ffmpeg ffprobe python3; do
  command -v "$c" >/dev/null || echo "cảnh báo: chưa có $c trên máy"
done
python3 -c "import numpy, PIL, playwright" 2>/dev/null || echo "cảnh báo: thiếu gói Python, chạy: pip install numpy pillow playwright"
python3 -c "import gtts" 2>/dev/null || echo "gợi ý: pip install gTTS để có giọng đọc tiếng Việt"
python3 -c "import whisper" 2>/dev/null || echo "gợi ý: pip install openai-whisper để căn lời chính xác hơn"
echo "xong. Mở phiên mới rồi nói: làm video dọc minh hoạ tài liệu <tên file>"
