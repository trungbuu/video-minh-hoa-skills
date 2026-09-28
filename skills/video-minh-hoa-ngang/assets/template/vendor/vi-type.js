/* ============================================================
   vi-type.js — ràng buộc ngắt dòng cho tiếng Việt
   ------------------------------------------------------------
   Tiếng Việt viết rời từng âm tiết nên trình duyệt sẵn sàng ngắt
   giữa hai âm tiết của một từ ghép, làm câu mất nghĩa tức thời
   (“lao ⏎ động”, “cá ⏎ nhân”, “điện ⏎ tử”). CSS không xử lý được
   việc này vì trình duyệt không biết ranh giới từ ghép tiếng Việt.

   Tệp này nối các âm tiết đó bằng khoảng trắng không ngắt (U+00A0),
   chỉ với danh sách từ ghép đã duyệt, nên không đoán sai.

   Hàm chạy được nhiều lần mà không hỏng, vì \s trong JavaScript
   đã bao gồm U+00A0 nên lần chạy sau không tạo thay đổi mới.
   ============================================================ */
(function (root) {
  "use strict";

  /* Từ ghép hai âm tiết xuất hiện trong nội dung của các trang.
     Chỉ thêm từ thật sự không được phép tách. */
  var PAIRS = [
    // pháp lý và tuân thủ
    "chứng minh","tuân thủ","quy định","nghị định","văn bản","pháp lý","chế tài",
    "hiệu lực","xử phạt","thời hiệu","phạm vi","áp dụng","căn cứ","ban hành",
    "thay thế","chuyển tiếp","tội phạm","nguyên tắc","thủ tục","trường hợp",
    "quyền lợi","trách nhiệm","bằng chứng","chứng cứ","mức phạt","khắc phục",
    // lao động và bảo hiểm
    "lao động","bảo hiểm","hợp đồng","thử việc","chấm dứt","tuyển dụng",
    "tiền lương","bảng lương","thời giờ","làm việc","làm thêm","nghỉ phép",
    "phép năm","nghỉ việc","điều chuyển","quyết toán","kỷ luật","nội quy",
    "đối thoại","thương lượng","thỏa ước","tập thể","đại diện","công đoàn",
    "thất nghiệp","chậm đóng","trốn đóng","đăng ký","điều chỉnh","xác nhận",
    "giấy phép","thu hồi","xuất cảnh","thanh lý","nước ngoài","đặc thù",
    "thành niên","cao tuổi","khuyết tật","giúp việc","gia đình","nhân sự",
    // an toàn và y tế
    "an toàn","vệ sinh","sức khỏe","tai nạn","môi trường","thiết bị",
    "huấn luyện","quan trắc","phương tiện","bảo vệ","khẩn cấp","rủi ro",
    // quản trị và vận hành
    "doanh nghiệp","tổ chức","hồ sơ","biểu mẫu","dữ liệu","phòng ban",
    "quản lý","quản trị","vận hành","kế toán","rà soát","kiểm tra","đối chiếu",
    "phát hiện","hoàn thành","cập nhật","theo dõi","ghi nhận","xác định",
    "đánh giá","phân công","triển khai","giải quyết","xây dựng","thực hiện",
    "sử dụng","bảo đảm","yêu cầu","phê duyệt","phụ trách","công việc",
    "đầu việc","nghiệp vụ","danh mục","tiến độ","nội bộ","định kỳ","bắt buộc",
    "khuyến nghị","tổng quan","tổng hợp","chi phí","thanh toán","công bố",
    "lưu trữ","truy cập","ứng viên","tài khoản","ủy quyền","chữ ký","điện tử",
    "cá nhân","lĩnh vực","thực tế","chính xác","phần việc","duy nhất",
    // nội dung chung của kênh
    "tài liệu","tham khảo","chia sẻ","chi tiết","tối ưu","bổ sung","dấu hiệu",
    "lãnh đạo","hỗ trợ","sự cố","tự bạch","toàn cảnh","bức tranh","trình duyệt",
    // bổ sung sau đợt quét khổ 390px và 1440px ngày 15/9/2026
    "hằng ngày","hằng tuần","hằng tháng","hằng quý","hằng năm","ngày tháng","năm trước",
    "thời gian","thời hạn","trước khi","đối với","tương đương","tương ứng","liên quan",
    "pháp luật","bộ luật","thông tư","công báo","điều khoản","điều kiện","quy chế",
    "quyết định","sửa đổi","thay đổi","hiện hành","vi phạm","xử lý","tố tụng","trục xuất",
    "tranh chấp","quấy rối","tình dục","cải chính","biên bản","báo cáo","thông báo",
    "thông tin","nội dung","kết quả","hình thức","hoạt động","hành động","hệ thống",
    "kiểm soát","phân quyền","bảo mật","cơ chế","cấu trúc","danh sách","bàn giao",
    "đối soát","khai trình","hành chính","tài chính","thu nhập","kinh phí","số tiền",
    "tiền lãi","bồi thường","trợ cấp","bồi dưỡng","chấm công","công khai","công tác",
    "chứng nhận","chứng từ","giấy tờ","lệ phí","môn bài","ngân hàng","khách hàng",
    "bên ngoài","tiếp cận","trí tuệ","đôn đốc","thường xuyên","ưu tiên","ưu đãi",
    "đi vắng","minh họa","định hướng","ứng cứu","nghiêm ngặt","nghề nghiệp","nuôi con",
    "việc làm","xã hội","Việt Nam","uỷ quyền","thỏa thuận","thoả thuận","thoả ước",
    // cụm ba âm tiết là một khái niệm, không để rớt âm tiết cuối
    "người lao động","người giúp việc","nơi làm việc","bệnh nghề nghiệp","chữ ký số",
    "chủ sở hữu","bất động sản","sử dụng lao động",
    // vai trò, nhóm và tần suất trong sổ tay tuân thủ
    "giám đốc","kỹ thuật","pháp chế","tư vấn","tư vấn thuế","hoá đơn","hóa đơn",
    "sở hữu trí tuệ","sở hữu","kiểm kê","khôi phục","sao lưu","giao dịch","lợi nhuận",
    "chính sách","sản phẩm","phiên bản","thuê bao","văn phòng","thành lập","tăng vốn",
    "duy trì","liên tục","đột xuất","diễn tập","gia hạn","văn bằng","thư viện",
    "nhà cung cấp","cung cấp","phân bổ","sai sót","khai thuế","giá trị gia tăng",
    "đóng sổ","bố trí","thay người","kỳ hạn",
    // landing page khoá học AI, bổ sung khi dựng Lazy AI Advanced ngày 15/9/2026
    "sưu tầm","công cụ","học viên","bài toán","quy trình","kỹ năng","tư duy","học phí",
    "buổi học","ghi hình","đầu ra","đầu vào","nghiệm thu","tiêu chí","phân rã","ngữ cảnh",
    "ví dụ","kết hợp","thế mạnh","đóng gói","tận dụng","thị trường","tiếp theo","hướng dẫn",
    "chuyển khoản","điện thoại","nâng cao","doanh thu","người mua","người đọc","nhân viên",
    "trợ lý","vấn đề","giải pháp","hiệu quả","phù hợp","chuẩn bị","trả phí","lặp lại",
    "bắt đầu","nhật ký","thương hiệu","chân dung","định dạng","tự động","cộng đồng",
    "hoàn tiền","liên hệ","câu hỏi","chương trình","lộ trình","kinh nghiệm","dược phẩm",
    "làm đẹp","điều hành","tra cứu","đồng hành","trọn bộ","dẫn đường","số liệu","sự thật",
    "chạy thử","thực hành","khảo sát","mô hình","song song","kiểm chứng","hậu quả",
    "lời khuyên","tiếp quản","phần mềm","trạng thái","nguồn gốc","bài tập","kế tiếp",
    "lỗi thời","phát sinh","chất liệu","tỉ lệ","email xác nhận","mạng xã hội","quà tặng",
    "Bửu Trung","Lazy AI","Lazy Team","Lazy News","Claude Code","Google Meet","Zalo OA",
    "cuối cùng","mỗi tuần","mỗi tháng","mỗi buổi","một lần","hai công cụ","lý thuyết",
    "phán đoán","con người","sản phẩm","thực chiến","bộ quy tắc","demo đối chứng",
    // video và phong cách hình ảnh
    "chuẩn hóa","trả lời","tự tin","chắc chắn","phong cách","tối giản","công nghệ",
    "sang trọng","thủ công","thập niên","đen trắng","sổ tay","còn tiếp","cắt giấy",
    "hoạt hình","nhạc nền","phụ đề","lời dẫn","chuyển động","nhịp điệu","ngành hàng"
  ];

  var LETTER = "A-Za-zÀ-ỹĐđ";
  /* đơn vị đi sau con số, không được rớt xuống dòng dưới */
  var UNIT = "năm|tháng|ngày|tuần|giờ|phút|lần|người|điều|khoản|chương|mục|nhóm|việc|triệu|tỷ|nghìn|đồng|%";
  /* nhãn văn bản pháp luật đi trước con số */
  var LABEL = "Điều|Khoản|Chương|Mục|Nghị định|Luật|Thông tư|Bộ luật|Case";

  var esc = function (s) { return s.replace(/ /g, "\\s"); };
  PAIRS = PAIRS.filter(function (v, i, a) { return a.indexOf(v) === i; })
               .sort(function (a, b) { return b.length - a.length; });
  var RE_PAIR  = new RegExp("(?<![" + LETTER + "])(" + PAIRS.map(esc).join("|") + ")(?![" + LETTER + "])", "giu");
  var RE_UNIT  = new RegExp("(\\d)\\s+(" + UNIT + ")(?![" + LETTER + "])", "giu");
  var RE_LABEL = new RegExp("(?<![" + LETTER + "])(" + LABEL + ")\\s+(\\d)", "gu");
  var RE_DATE  = new RegExp("(?<![" + LETTER + "])(ngày|từ ngày|đến ngày)\\s+(\\d)", "giu");
  var NB = "\u00A0";

  /* Không đụng vào logo, wordmark, mã và ô nhập liệu. */
  var SKIP = "script,style,code,pre,textarea,input,select,.lz,.wm,.mono";

  function bind(scope) {
    var start = scope || document.body;
    if (!start) return 0;
    var walker = document.createTreeWalker(start, NodeFilter.SHOW_TEXT, {
      acceptNode: function (node) {
        var el = node.parentElement;
        if (!el || el.closest(SKIP)) return NodeFilter.FILTER_REJECT;
        if (!node.nodeValue || node.nodeValue.indexOf(" ") === -1) return NodeFilter.FILTER_REJECT;
        return NodeFilter.FILTER_ACCEPT;
      }
    });
    var node, changed = 0;
    while ((node = walker.nextNode())) {
      var before = node.nodeValue;
      var after = before
        .replace(RE_PAIR,  function (m) { return m.replace(/\s/g, NB); })
        .replace(RE_UNIT,  function (m, a, b) { return a + NB + b; })
        .replace(RE_LABEL, function (m, a, b) { return a + NB + b; })
        .replace(RE_DATE,  function (m, a, b) { return a.replace(/\s/g, NB) + NB + b; });
      if (after !== before) { node.nodeValue = after; changed++; }
    }
    return changed;
  }

  root.viType = { bind: bind, pairs: PAIRS };

  /* Trang tĩnh chạy ngay. Trang React gọi lại viType.bind() sau mỗi lần vẽ. */
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () { bind(); });
  } else {
    bind();
  }
})(window);
