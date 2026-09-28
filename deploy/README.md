# Đưa trang hướng dẫn lên WordPress

`toiuu-wordpress.html` là trang hướng dẫn gói trong một file, sẵn sàng dán vào WordPress theo chế độ trang độc lập.

- Toàn bộ nội dung nằm trong một khối `<!-- wp:html --> ... <!-- /wp:html -->`, nên WordPress không chèn thẻ `<p>` vào CSS hay JavaScript.
- CSS gom trong lớp `.vmh`, kèm vài dòng chặn CSS của theme lấn vào.
- Script gắn `data-no-optimize="1"` để LiteSpeed không trì hoãn.
- Video và ảnh mẫu lấy qua jsDelivr từ thư mục `docs/media` của repo này, không cần tải lên thư viện media.
- Trang chỉ có một thẻ H1.

Cách đăng với skill wordpress-mcp: tạo `page` ở trạng thái nháp với nội dung là toàn bộ file, đặt template `elementor_canvas`, đọc lại trường template để xác nhận, kiểm URL ở desktop và mobile rồi mới publish.
