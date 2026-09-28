# Video minh hoạ tài liệu, hai skill cho Claude Code

Hai skill biến một tài liệu thành video hoạt hình có giọng đọc tiếng Việt, phụ đề karaoke khớp từng từ, nhạc nền và nhận diện thương hiệu. Không dùng model AI tạo video, không cần khoá API. Bạn chỉ cần đưa tài liệu và trả lời bốn câu hỏi, Claude viết kịch bản, dựng, tự soát và nghiệm thu.

| Skill | Khổ | Hợp với |
|---|---|---|
| [`video-minh-hoa-doc`](skills/video-minh-hoa-doc/SKILL.md) | dọc 9:16, 1080×1920 | TikTok, Reels, Shorts, Zalo, xem trên điện thoại |
| [`video-minh-hoa-ngang`](skills/video-minh-hoa-ngang/SKILL.md) | ngang 16:9, 1920×1080 | YouTube, đào tạo, màn hình chiếu, website |

Hướng dẫn trực quan có video mẫu: [docs/index.html](docs/index.html) (bật GitHub Pages thư mục `docs` để xem trên web).

## Cài đặt

```bash
git clone https://github.com/trungbuu/video-minh-hoa-skills.git
cd video-minh-hoa-skills
./install.sh            # chép hai skill vào ~/.claude/skills
```

Hoặc chép tay thư mục `skills/video-minh-hoa-doc` và `skills/video-minh-hoa-ngang` vào `~/.claude/skills/`.

## Cần có trên máy

| Thành phần | Bắt buộc | Cài |
|---|---|---|
| Node.js 18+ | có | nodejs.org; HyperFrames chạy qua `npx`, tự tải Chrome headless lần đầu |
| ffmpeg và ffprobe | có | `brew install ffmpeg` hoặc `winget install Gyan.FFmpeg` |
| Python 3.9+ với numpy, Pillow, playwright | có | `pip install numpy pillow playwright` |
| gTTS | nên có | `pip install gTTS`, giọng đọc tiếng Việt, cần mạng; thiếu thì dùng macOS `say` |
| openai-whisper, model `base` | nên có | `pip install openai-whisper`, căn lời từng từ chính xác hơn |

## Dùng thử

Mở Claude Code trong một thư mục trống, đặt tài liệu vào đó rồi gõ:

```
Làm video dọc 45 giây minh hoạ tài liệu quy-trinh-hoan-tien.md cho nhân viên mới
```

Claude đọc tài liệu, hỏi bốn câu, đề xuất kế hoạch, chờ bạn đồng ý rồi dựng. Kết quả nằm trong `renders/` của dự án: bản có giọng, bản không lời, bản nén social và file phụ đề `.srt`.

## Cấu trúc repo

```text
skills/video-minh-hoa-doc/     skill khổ dọc
skills/video-minh-hoa-ngang/   skill khổ ngang
  SKILL.md                     quy trình 6 bước cho Claude
  references/kich-ban.md       cách viết script.json, 6 kiểu cảnh
  assets/template/             template HTML, engine story.js, scene kit, brand.css
  assets/pipeline/             công cụ giọng, căn lời, âm thanh, tự soát, render
  scripts/                     new_project, check_script, pipeline, qa_video
docs/                          trang hướng dẫn và video mẫu
licenses/                      giấy phép phông chữ
```

## Giấy phép

Mã nguồn theo giấy phép MIT, xem [LICENSE](LICENSE). Phông Be Vietnam Pro theo SIL Open Font License 1.1, xem [licenses/BeVietnamPro-OFL.txt](licenses/BeVietnamPro-OFL.txt). HyperFrames (Apache-2.0), GSAP, whisper và gTTS không nằm trong repo, được tải khi chạy.
