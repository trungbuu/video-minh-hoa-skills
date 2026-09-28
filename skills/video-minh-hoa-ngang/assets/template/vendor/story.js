// story.js, engine chung của template kể chuyện khổ dọc (motion-video-vi v2).
// Bảng màu đọc từ biến CSS nên đổi thương hiệu chỉ cần sửa brand.css.
// Mọi thứ là hàm thuần của t: không Math.random, không Date, không trạng thái tích luỹ giữa các khung.
// Mốc lấy từ window.CUES (tools/layout.py) và window.ENV (đường bao lời, tools/make_audio.py).
(function () {
  // Nạp sẵn mọi phông khai báo trong fonts.css ngay từ đầu. Phông chia theo unicode-range chỉ tải khi chữ
  // cần tới xuất hiện, nên nếu không nạp trước thì khung đầu của một câu có dấu có thể render bằng phông dự phòng.
  if (document.fonts && document.fonts.forEach) document.fonts.forEach((f) => { try { f.load(); } catch (e) { /* bỏ qua */ } });
  const { el } = window.StickRig;
  const L = window.Lib;
  const { clamp, lerp, prog, eo, eio, TAU } = L;
  const CUES = window.CUES, BEATS = window.BEATS || [], ENV = window.ENV || [];
  const DUR = CUES.duration, SC = CUES.scenes, BEAT = 60 / CUES.bpm;
  const NB = " ";
  const css = getComputedStyle(document.documentElement);
  const v = (n, d) => (css.getPropertyValue(n) || "").trim() || d;
  const P = {
    red: v("--accent", "#D93644"), red2: v("--accent-2", "#FF6B6B"), ink: v("--ink", "#4A4A4A"), ink2: v("--ink-2", "#2E2E2E"),
    decor: v("--decor", "#E0E0E0"), soft: v("--card", "#F5F5F5"), wm: v("--wm", "#F2F2F2"), bg: v("--bg", "#FFFFFF"),
    olive: v("--nature", "#7C8F5B"), oliveSoft: v("--nature-soft", "#E4EAD8"),
    skin: v("--skin", "#F4D3BC"), skin2: v("--skin-2", "#E8BC9A"), hair: v("--hair", "#2B2522"),
  };
  P.accent = P.red; P.accent2 = P.red2;

  // ---------- thời gian ----------
  function beatPulse(t) {
    let s = 0;
    for (const [bt, st] of BEATS) { if (t >= bt && t - bt < 0.5) s += st * Math.exp(-(t - bt) / 0.14); }
    return clamp(s);
  }
  const win = (t, a, b, fi = 0.45, fo = 0.35) => Math.min(prog(t, a, fi), 1 - prog(t, b - fo, fo));
  const sceneAt = (t) => { let i = 0; SC.forEach((s, k) => { if (t >= s) i = k; }); return i; };
  const sceneEnd = (sc) => (sc + 1 < SC.length ? SC[sc + 1] : DUR + 1);
  const fold = (s) => s.replace(/[_\u00a0]/g, " ").normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/đ/g, "d").replace(/Đ/g, "D")
    .toLowerCase().replace(/[^a-z0-9 ]/g, " ").replace(/\s+/g, " ").trim();
  // so nguyên âm tiết liền nhau, nên “ba” không khớp nhầm “bạn”
  const sylMatch = (key, w) => { const k = key.split(" ").filter(Boolean), t = w.split(" ").filter(Boolean);
    for (let i = 0; i + k.length <= t.length; i++) if (k.every((x, j) => t[i + j] === x)) return true; return false; };
  /** Mốc bắt đầu của từ `word` (lần thứ nth) trong dòng lời `line`. Không thấy thì cảnh báo và trả về đầu dòng. */
  function W(line, word, nth = 1) {
    const ws = (CUES.words || {})[String(line)] || [];
    const key = fold(word); let seen = 0;
    for (const [w, s] of ws) if (sylMatch(key, fold(w.replace(/_/g, " ").replace(/\u00a0/g, " "))) && ++seen === nth) return s;
    const l = (CUES.lines || []).find((x) => x.i === line);
    if (!W._warned) { W._warned = {}; }
    if (!W._warned[line + word]) { console.warn(`W(${line}, "${word}") không thấy, dùng đầu dòng`); W._warned[line + word] = 1; }
    return l ? l.v : 0;
  }
  function WE(line, word, nth = 1) {
    const ws = (CUES.words || {})[String(line)] || [];
    const key = fold(word); let seen = 0;
    for (const [w, , e] of ws) if (sylMatch(key, fold(w.replace(/_/g, " ").replace(/\u00a0/g, " "))) && ++seen === nth) return e;
    return W(line, word, nth) + 0.4;
  }
  /** Mốc bắt đầu của dòng lời thứ k trong cảnh sc. */
  const lineAt = (sc, k = 0) => { const l = (CUES.lines || []).filter((x) => x.sc === sc)[k]; return l ? l.v : SC[sc] + 1.5 * k; };
  /** Độ mở miệng 0..1 từ đường bao lời, để nhân vật nói theo tiếng. */
  const envAt = (t) => { const i = Math.floor(t * 30); return i >= 0 && i < ENV.length ? ENV[i] : 0; };
  const hitNear = (t, span = 0.5) => (CUES.hits || []).reduce((m, h) => (t >= h && t - h < span ? Math.max(m, 1 - (t - h) / span) : m), 0);

  // ---------- chữ ----------
  const J = (s) => (s || "").replace(/_/g, NB);
  const bindVi = (n) => window.viType && window.viType.bind && n && window.viType.bind(n);
  const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;");
  const rich = (s) => esc(J(s)).replace(/\[(.+?)\]/g, '<span class="g">$1</span>');

  // ---------- nền ----------
  function stageBase(svg) {
    const defs = el("defs", {}, svg);
    defs.innerHTML = `<linearGradient id="vit" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="${P.red}"/><stop offset="1" stop-color="${P.red2}"/></linearGradient>
      <radialGradient id="glow"><stop offset="0" stop-color="${P.red2}" stop-opacity="0.10"/><stop offset="1" stop-color="${P.red2}" stop-opacity="0"/></radialGradient>
      <filter id="soft" filterUnits="userSpaceOnUse" x="-200" y="-200" width="1480" height="2320"><feDropShadow dx="0" dy="10" stdDeviation="14" flood-color="#000" flood-opacity="0.08"/></filter>`;
    el("rect", { width: 1080, height: 1920, fill: P.bg }, svg);
    const glow = el("circle", { cx: 860, cy: 980, r: 620, fill: "url(#glow)" }, svg);
    const wm = el("text", { x: 1180, y: 1500, "text-anchor": "end", "font-size": 1250, fill: P.wm, class: "wm" }, svg);
    const cam = el("g", {}, svg);
    return { defs, glow, wm, cam };
  }

  // ---------- nhân vật và đạo cụ ----------
  const COACH = { skin: P.skin, hair: P.hair, hairStyle: "bun", exprs: ["smile", "happy", "think", "grin"], badge: [P.red, "diamond"] };
  const COACH2 = { skin: P.skin2, hair: P.hair, hairStyle: "short", exprs: ["smile", "happy", "grin", "think"], badge: [P.red, "diamond"] };
  const CLIENT = { skin: P.skin, hair: "#5A4636", hairStyle: "long", exprs: ["smile", "worried", "happy", "think", "grin"], badge: [P.ink, "circle"] };
  // Bọc expr: tên biểu cảm không có trong spec.exprs thì dùng biểu cảm đầu tiên, tránh lỗi đầu nhân vật mất mắt.
  const person = (parent, spec) => {
    const p = L.person(parent, spec), ok = new Set(spec.exprs || ["smile"]), raw = p.expr.bind(p);
    p.expr = (n) => raw(ok.has(n) ? n : (spec.exprs || ["smile"])[0]);
    return p;
  };
  /** Nói theo tiếng: đổi giữa mặt cười và mặt há miệng theo đường bao lời trong khoảng [a, b). */
  const talk = (p, t, a, b, base = "smile", open = "grin") => p.expr(t >= a && t < b && envAt(t) > 0.42 ? open : base);

  function squat(t, u) {
    return { hip: [lerp(0, -18, u), lerp(0, 44, u)], lean: lerp(0, 24, u),
      legs: [[lerp(7, 88, u), lerp(3, -8, u)], [lerp(-7, 84, u), lerp(-3, -12, u)]],
      arms: [[lerp(14, 84, u), lerp(6, 92, u)], [lerp(-14, 78, u), lerp(-6, 86, u)]], headTilt: lerp(0, -10, u) };
  }
  function point(t, u) { const p = L.stand(t); p.arms[0] = [lerp(14, 62, u), lerp(6, 68, u)]; p.lean = 3 * u; return p; }
  function holdItem(t) { const p = L.stand(t); p.arms[0] = [40, 118]; return p; }
  function wave(t, u) { const p = L.stand(t), w = Math.sin(TAU * 2 * t); p.arms[0] = [lerp(14, 64, u), lerp(6, 150 + 18 * w, u)]; return p; }
  function clipboard(parent) {
    const g = el("g", {}, parent);
    el("rect", { x: -34, y: -46, width: 68, height: 90, rx: 8, fill: "#fff", stroke: "#1b1b1b", "stroke-width": 4.5 }, g);
    el("rect", { x: -16, y: -54, width: 32, height: 14, rx: 4, fill: P.red }, g);
    [-18, -2, 14].forEach((y, i) => el("rect", { x: -20, y, width: i === 2 ? 26 : 40, height: 7, rx: 3.5, fill: P.decor }, g));
    return g;
  }
  const ground = (g, x0 = 150, x1 = 930, y = 1150) => el("line", { x1: x0, x2: x1, y1: y + 2, y2: y + 2, stroke: P.decor, "stroke-width": 4, "stroke-linecap": "round" }, g);

  // ---------- lớp chữ HTML ----------
  const $ = (id) => document.getElementById(id);
  const kicker = $("kicker"), head = $("headline"), sub = $("subhead"), titleBox = $("title"), cap = $("caption");
  const chipsBox = $("chips"), dotsBox = $("dots"), endcard = $("endcard"), answer = $("answer");
  // Phụ đề: mỗi từ có mốc thật từ bộ căn lời. Bản cũ không có cap.w thì chia đều như v1.
  const CAPS = CUES.caps.map((c) => {
    if (c.w && c.w.length) return { a: c.a, b: c.b, w: c.w.map((x) => J(x[0])), ts: [...c.w.map((x) => x[1]), c.w[c.w.length - 1][2]] };
    const w = J(c.s).split(" "), wt = w.map((x) => x.split(NB).length + 0.35), sum = wt.reduce((m, x) => m + x, 0);
    let acc = 0; const ts = wt.map((x) => { const q = c.v + (acc / sum) * c.d * 0.95; acc += x; return q; });
    return { a: c.a, b: c.b, w, ts: [...ts, c.v + c.d * 0.95] };
  });
  // Thẻ kết điền từ meta.cta trong script.json: kicker, headline (có [từ nhấn]), rows [[nhãn, giá trị], ...]
  const CTA = (window.META || {}).cta || {};
  if (endcard && CTA.headline) {
    const q = (s) => endcard.querySelector(s);
    if (q(".ec-k")) q(".ec-k").textContent = J(CTA.kicker || "");
    if (q(".ec-h")) q(".ec-h").innerHTML = rich(CTA.headline).replace(/\n/g, "<br>");
    if (q(".ec-card")) q(".ec-card").innerHTML = (CTA.rows || []).map(([k, x]) => `<div class="ec-row"><span>${esc(J(k))}</span><b>${esc(J(x))}</b></div>`).join("");
  }
  if (endcard) bindVi(endcard);

  /** cfg: { titles:[{k,h,s,big,mid}], chips:[[...]], chipAt:(sc)=>giây, answers:[{text, at}], dots:(sc,t)=>[...], letters, hideTitle:(sc)=>bool } */
  function makeText(cfg) {
    let titleKey = -1, capKey = -1, chipKey = -1, ansKey = -1, spans = [], chipEls = [];
    if (dotsBox) dotsBox.innerHTML = (cfg.letters || "").split("").map((c) => `<span>${c}</span>`).join("");
    const dotEls = dotsBox ? Array.from(dotsBox.children) : [];
    return function renderText(t, bp, sc) {
      const T = cfg.titles[sc] || { h: "" };
      if (sc !== titleKey) {
        kicker.textContent = J(T.k || ""); head.innerHTML = rich(T.h || ""); sub.innerHTML = rich(T.s || "");
        head.className = T.big ? "big" : T.mid ? "mid" : ""; bindVi(titleBox); titleKey = sc;
      }
      const a = SC[sc], b = sceneEnd(sc);
      const tv = cfg.hideTitle && cfg.hideTitle(sc) ? 0 : win(t, a + 0.05, b, 0.4, 0.3);
      titleBox.style.opacity = tv.toFixed(3);
      titleBox.style.transform = `translateX(${(-40 * (1 - eo(prog(t, a + 0.05, 0.6)))).toFixed(1)}px)`;
      head.style.transform = `scale(${(1 + 0.018 * bp).toFixed(4)})`;
      sub.style.opacity = prog(t, a + 0.35, 0.4).toFixed(3);

      const list = (cfg.chips && cfg.chips[sc]) || [];
      if (sc !== chipKey) {
        chipsBox.innerHTML = list.map((c) => `<div class="chip">${esc(J(c))}</div>`).join("");
        chipEls = Array.from(chipsBox.children); bindVi(chipsBox); chipKey = sc;
        chipsBox.style.transform = "none";
        // cộng bề rộng từng chip: khi hàng chip tràn và căn giữa, scrollWidth bỏ sót phần tràn bên trái
        const gap = parseFloat(getComputedStyle(chipsBox).columnGap) || 18;
        const sw = chipEls.reduce((m, c) => m + c.offsetWidth, 0) + gap * Math.max(0, chipEls.length - 1), cw = chipsBox.clientWidth || 840;
        chipsBox.dataset.k = sw > cw ? (cw / sw).toFixed(4) : "1";
      }
      const t0 = cfg.chipAt ? cfg.chipAt(sc) : a + 2.0;
      chipEls.forEach((c, i) => {
        const at = Array.isArray(t0) ? t0[i] : t0 + i * 2 * BEAT;
        const u = prog(t, at, 0.35);
        c.style.opacity = Math.min(u * 1.5, 1 - prog(t, b - 0.3, 0.3)).toFixed(3);
        c.style.transform = `translateY(${(26 * (1 - eo(u))).toFixed(1)}px) scale(${(0.9 + 0.1 * L.back(u)).toFixed(3)})`;
      });
      chipsBox.style.transform = `scale(${chipsBox.dataset.k || 1})`;

      if (answer) {
        const A = cfg.answers && cfg.answers[sc];
        if (sc !== ansKey) { answer.innerHTML = A ? `<span class="tick">✓</span><span>${esc(J(A.text))}</span>` : ""; bindVi(answer); ansKey = sc; }
        const u = A ? prog(t, A.at, 0.4) : 0;
        answer.style.opacity = (A ? Math.min(u * 1.6, 1 - prog(t, b - 0.3, 0.3)) : 0).toFixed(3);
        answer.style.transform = `translateX(-50%) scale(${(A ? 0.85 + 0.15 * L.back(u) : 1).toFixed(3)})`;
      }

      if (cfg.dots && dotsBox) {
        const st = cfg.dots(sc, t);
        dotEls.forEach((d, i) => { d.className = st[i] || ""; });
        dotsBox.style.opacity = cfg.dotsVisible ? cfg.dotsVisible(t).toFixed(3) : "1";
      }

      const ci = CAPS.findIndex((g) => t >= g.a && t < g.b);
      if (ci !== capKey) {
        cap.innerHTML = ci < 0 ? "" : CAPS[ci].w.map((w) => `<span class="w">${esc(w)}</span>`).join(" ");
        spans = Array.from(cap.querySelectorAll(".w")); capKey = ci; bindVi(cap);
      }
      if (ci >= 0) {
        const g = CAPS[ci];
        spans.forEach((s, i) => { s.className = "w" + (t >= g.ts[i] ? " on" : "") + (t >= g.ts[i] && t < g.ts[i + 1] ? " now" : ""); });
        cap.style.opacity = Math.min(prog(t, g.a, 0.2), 1 - prog(t, DUR - 0.5, 0.4)).toFixed(3);
      }
      if (endcard) {
        const e = prog(t, CUES.ending + 0.1, 0.7);
        endcard.style.opacity = e.toFixed(3);
        endcard.style.transform = `translateY(${(30 * (1 - eo(prog(t, CUES.ending + 0.1, 1.0)))).toFixed(1)}px)`;
      }
    };
  }

  function finish(renderAt, style = "story") {
    renderAt(0);
    window.renderAt = renderAt;
    window.VIDEO = { total: DUR, fps: 30, style };
    const clock = { t: 0 };
    const tl = gsap.timeline({ paused: true });
    tl.to(clock, { t: DUR, duration: DUR, ease: "none", onUpdate: () => renderAt(clock.t) }, 0);
    window.StyleLab = { timeline: tl, style };
  }

  window.Story = { P, CUES, DUR, SC, BEAT, NB, beatPulse, win, sceneAt, sceneEnd, W, WE, lineAt, envAt, hitNear, J, bindVi, rich,
    stageBase, person, talk, COACH, COACH2, CLIENT, squat, point, holdItem, wave, clipboard, ground, makeText, finish };
})();
