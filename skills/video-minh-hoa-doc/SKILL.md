---
name: video-minh-hoa-doc
description: Biến một tài liệu thành video hoạt hình dọc 9:16 (1080×1920) từ 20 đến 90 giây có giọng đọc tiếng Việt, phụ đề karaoke khớp từng từ, nhạc nền và nhận diện thương hiệu, cho TikTok, Reels, Shorts, Zalo. Chỉ cần viết script.json theo 6 kiểu cảnh có sẵn, không viết code, không cần khoá API; có bộ kiểm kịch bản, tự soát khung hình và cổng nghiệm thu bằng số. Dùng khi người dùng muốn minh hoạ một quy trình, chính sách, hướng dẫn, bài học hay thông tin cần thiết thành video dọc, hoặc nói “làm video dọc từ tài liệu này”, “làm Reels giải thích”, “video TikTok hoạt hình”.
---

# Video minh hoạ tài liệu, khổ dọc 9:16

Biến một tài liệu (quy trình, chính sách, hướng dẫn, báo cáo, bài giảng, trang sản phẩm) thành video hoạt hình dọc 1080×1920 có giọng đọc tiếng Việt, phụ đề karaoke khớp từng từ, nhạc nền và âm thanh nhấn. Hình là nhân vật người que và đạo cụ vẽ bằng SVG, màu và phông theo thương hiệu. Không dùng model AI tạo video, không cần khoá API.

Khổ dọc hợp với TikTok, Reels, YouTube Shorts, Zalo và xem trên điện thoại. Skill tự chừa vùng an toàn cho giao diện các ứng dụng này: 220 px phía trên, 470 px phía dưới, không đặt chữ ở x > 950 trong đoạn y 880 đến 1450. Cần khổ ngang cho YouTube, màn hình chiếu, website thì dùng skill `video-minh-hoa-ngang`.

Đường dẫn trong skill tính từ thư mục chứa file này, ký hiệu `<skill>`.

## Khi nào không dùng

Không dùng khi cần cảnh quay thật, khuôn mặt thật, khẩu hình khớp lời hay chuyển động mềm như vải, nước. Khi đó nói rõ với người dùng thay vì cố dựng bằng SVG.

## Nguyên tắc

1. Chỉ dùng thông tin có trong tài liệu người dùng đưa. Mỗi con số, mỗi nhận định trên màn hình phải truy được về tài liệu; ghi vào `facts.md` của dự án. Số minh hoạ thì ghi rõ “ví dụ”.
2. Hỏi đủ bốn câu và chờ người dùng đồng ý kế hoạch trước khi tạo giọng. Bốn câu gồm có: video để làm gì, ai xem, đăng ở đâu, xem xong người xem nên làm gì.
3. Không viết code cảnh. Mọi thứ nằm trong `script.json` theo [references/kich-ban.md](references/kich-ban.md).
4. Chỉ giao video khi cổng nghiệm thu báo ĐẠT, và báo lại bằng số đo.
5. Không bật máy đọc trả phí, không tải model hay phần mềm mới khi chưa hỏi. Không in khoá API.
6. Không dùng khuôn mặt, tên thật hay logo của bên thứ ba khi chưa có đồng ý.
7. Mọi đầu ra nằm trong thư mục dự án của người dùng, không ghi vào thư mục skill.

## Quy trình 6 bước

1. **Đọc tài liệu.** Tóm tắt trong 3 câu, ghi `facts.md` mỗi dòng một ý kèm vị trí trong tài liệu.
2. **Chốt kế hoạch.** Hỏi bốn câu ở nguyên tắc 2. Đề xuất trong 4 đến 6 câu gồm thông điệp chính, số cảnh, độ dài ước tính, lời mời cuối. Chờ đồng ý.
3. **Tạo dự án.** `python3 <skill>/scripts/new_project.py <thư mục> [--brand brand.css --logo logo.png --mark dau.png]`. Không có brand thì dùng màu trung tính có sẵn.
4. **Viết kịch bản.** Viết `script.json` theo [references/kich-ban.md](references/kich-ban.md), dùng ít nhất 3 kiểu cảnh khác nhau. Chạy `python3 <skill>/scripts/check_script.py <thư mục> --target <giây>` tới khi ĐẠT.
5. **Dựng.** `python3 <skill>/scripts/pipeline.py <thư mục> --name <tên-video> --social`. Lệnh chạy lần lượt kiểm kịch bản, tạo giọng, căn lời, âm thanh, đo cân bằng, đo phách, lint, tự soát, render, phụ đề, nghiệm thu. Bước nào lỗi thì dừng; đọc lỗi, sửa, chạy lại với `--from <bước>`.
6. **Giao.** Mở `review/self-eval.png` xem một lượt. Giao bản có giọng, bản không lời, bản nén social và file `.srt` trong `renders/`. Ghi một mục vào `project.md` gồm quyết định và việc còn treo.

## Kết quả nhận được

| File | Dùng khi |
|---|---|
| `renders/<tên>_1080x1920_giong-doc.mp4` | bản gốc có giọng đọc |
| `renders/<tên>_1080x1920_social.mp4` | đăng mạng xã hội, dung lượng nhỏ |
| `renders/<tên>_1080x1920_khong-loi.mp4` | lồng giọng người thật hoặc chỉ cần nhạc |
| `renders/<tên>.srt` | tải phụ đề lên nền tảng |
| `review/self-eval.png` | tấm ghép khung hình kèm dạng sóng để duyệt nhanh |

Chuẩn nghiệm thu gồm có: đúng khổ 1080x1920, 30 fps, AAC 48 kHz stereo, -14 LUFS ± 1, đỉnh thật từ -1 dBTP trở xuống, không khung đen, nhạc thấp hơn lời 4 đến 6 dB, tự soát 0 lỗi.

## Đổi gì chạy lại từ đâu

| Đã đổi | Lệnh |
|---|---|
| lời đọc | `pipeline.py <thư mục> --from voice` |
| neo, độ dài cảnh | `--from layout` |
| mức nhạc | `--from audio` |
| chữ trên màn hình, màu, phông, kiểu cảnh | `--from data` |

## Lỗi hay gặp

| Lỗi | Cách xử lý |
|---|---|
| `check_script` báo chữ quá dài | rút gọn, tách cảnh; không thu nhỏ chữ |
| `NEO HOẶC JS: W(...) không thấy` | từ neo phải có nguyên văn trong phụ đề của dòng đó |
| `CỘT PHẢI BỊ NÚT CHE`, `VÙNG AN TOÀN` | rút ngắn chip hay tiêu đề; chữ khổ dọc phải tránh vùng nút của ứng dụng |
| máy đọc sai tên tiếng Anh, số | viết trường `tts` với đoạn `["en", ...]` hoặc số bằng chữ |
| giọng máy nghe đều đều | chạy `VOICE_ENGINE=say` thử giọng khác, hoặc hỏi người dùng có muốn dùng dịch vụ trả phí |

## Môi trường

Cần Node.js 18 trở lên (chạy HyperFrames qua `npx`), ffmpeg và ffprobe, Python 3.9 trở lên với numpy, Pillow, playwright. Nên có gTTS (giọng đọc, cần mạng) và openai-whisper với model `base` đã tải (căn lời chính xác hơn). Thiếu whisper thì skill tự dùng bộ căn theo năng lượng; thiếu gTTS thì dùng macOS `say`. Lần đầu HyperFrames tự tải Chrome headless.

## Tài nguyên

| Đường dẫn | Nội dung |
|---|---|
| `references/kich-ban.md` | cách viết script.json, 6 kiểu cảnh, neo theo từ, đổi thương hiệu |
| `assets/template/` | template dọc 1080×1920, engine `vendor/story.js`, scene kit, `brand.css` |
| `assets/pipeline/` | công cụ được chép vào `tools/` của mỗi dự án |
| `scripts/` | `new_project.py`, `check_script.py`, `pipeline.py`, `qa_video.py` |
