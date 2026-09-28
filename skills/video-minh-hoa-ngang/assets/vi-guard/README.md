# vi-guard

Bộ công cụ đi kèm quy tắc số 11 trong `~/.claude/CLAUDE.md`, dùng khi dựng HTML tiếng Việt.

`vi-type.js` nối các âm tiết của từ ghép, số với đơn vị, nhãn điều khoản với con số và chữ “ngày” với ngày tháng bằng khoảng trắng không ngắt U+00A0. Trang tĩnh chỉ cần nạp tệp. Trang React gọi `window.viType.bind()` trong một `useEffect` không có mảng phụ thuộc, vì mỗi lần React vẽ lại thì chuỗi gốc quay về.

`vi-audit.js` đo điểm ngắt dòng thật trên trang đã dựng và báo bốn loại lỗi là tách từ ghép, widow, line-height dưới 1 và tràn ngang. Chạy ở 390px và 1440px, mở hết mọi trạng thái giao diện, chỉ nghiệm thu khi `soLoi` bằng 0.

Khi bộ đo báo một từ ghép bị tách mà từ đó chưa có trong danh sách, thêm vào mảng `PAIRS` của `vi-type.js` rồi chép bản mới vào dự án. Không chèn `&nbsp;` bằng tay vào dữ liệu.

Bản gốc của hai tệp được kiểm chứng trên `buutrung-compliance.pages.dev` ngày 15/9/2026, với 289 cụm từ.
