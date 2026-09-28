/* ============================================================
   vi-audit.js — đo ngắt dòng tiếng Việt trên trang đã dựng
   ------------------------------------------------------------
   Chạy trong console trình duyệt hoặc công cụ javascript của agent,
   sau khi trang đã nạp vi-type.js:

     await viAudit()                              // chỉ quét trạng thái hiện tại
     await viAudit(async (scan, click, wait) => { // quét qua nhiều trạng thái
       click(document.querySelectorAll('nav button')[1]); await wait(300);
       await scan('tab 2');
     })

   Chạy ở hai khổ 390px và 1440px, mở hết tab, accordion, modal, drawer.
   Chỉ nghiệm thu khi soLoi = 0.

   Lỗi được tính:
   - TÁCH       điểm ngắt dòng nằm bên trong một cụm mà vi-type lẽ ra phải nối
   - WIDOW      dòng cuối chỉ còn một từ ngắn trơ trọi
   - LINE-HEIGHT tiêu đề có dấu tiếng Việt mà line-height dưới 1
   - TRÀN NGANG  trang rộng hơn khung nhìn
   Điểm ngắt giữa hai từ ghép khác nhau (“thực hiện ⏎ hành vi”) hoặc sau
   dấu phẩy là hợp lệ, bộ đo không báo.
   ============================================================ */
window.viAudit = async function (scenario) {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const click = el => el && el.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  const P = (window.viType && window.viType.pairs) || [];
  if (!P.length) return { loi: ["Trang chưa nạp vi-type.js"] };
  const LET = "A-Za-zÀ-ỹĐđ";
  const RE = new RegExp("(?<![" + LET + "])(" + P.map(x => x.replace(/ /g, "[\\s\\u00A0]")).join("|") + ")(?![" + LET + "])", "giu");
  const S = "h1,h2,h3,h4,p,li,span,b,small,td,th,button,a,div,strong,em,label";
  const found = new Set();

  const breaks = el => {
    const pos = [], r = document.createRange(); let prev = null, off = 0, text = "";
    for (const n of el.childNodes) {
      if (n.nodeType !== 3) continue;
      const s = n.nodeValue;
      for (let i = 0; i < s.length; i++) {
        r.setStart(n, i); r.setEnd(n, i + 1);
        const b = r.getBoundingClientRect();
        if (b.height) { if (prev !== null && Math.abs(b.top - prev) > 2) pos.push(off + i); prev = b.top; }
      }
      text += s; off += s.length;
    }
    return { text, pos };
  };

  const scan = async tag => {
    await document.fonts.ready; await wait(350);
    if (window.viType) window.viType.bind();
    await wait(120);
    for (const el of document.querySelectorAll(S)) {
      if (el.querySelector(S) || el.closest(".lz,.wm")) continue;
      if (!el.getBoundingClientRect().width) continue;
      const { text, pos } = breaks(el);
      if (!pos.length) continue;
      for (const m of text.matchAll(RE)) {
        const a = m.index, b = a + m[0].length;
        for (const p of pos) if (p > a && p < b) found.add("TÁCH " + m[0].replace(/ /g, " ") + " @" + (el.className || el.tagName) + " (" + tag + ")");
      }
      const last = text.slice(pos[pos.length - 1]).trim();
      if (!/\s/.test(last) && last.length < 12 && !/^[\d.,%–\-/→]+$/.test(last))
        found.add("WIDOW " + last + " @" + (el.className || el.tagName) + " (" + tag + ")");
    }
    for (const el of document.querySelectorAll("h1,h2,h3,h4")) {
      const cs = getComputedStyle(el), k = parseFloat(cs.lineHeight) / parseFloat(cs.fontSize);
      if (k < 1 && /[À-ỹ]/.test(el.textContent)) found.add("LINE-HEIGHT " + (el.className || el.tagName) + " " + k.toFixed(2));
    }
    if (document.documentElement.scrollWidth > innerWidth) found.add("TRÀN NGANG (" + tag + ")");
  };

  await scan("trạng thái đầu");
  if (typeof scenario === "function") await scenario(scan, click, wait);
  return { trang: location.pathname, kho: innerWidth, soLoi: found.size, loi: [...found].slice(0, 30) };
};
