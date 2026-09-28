// Thư viện dùng chung cho cả bản ngang và bản dọc: tiện ích thời gian, nhân vật, tư thế,
// đồ vật và phần điều phối thẻ tiêu đề, nhãn cảnh, phụ đề. Mỗi bản chỉ khác nhau ở bố cục cảnh.
(function () {
  const { el, createFigure, poseFigure } = window.StickRig;
  const H = window.Heads, INK = H.INK;
  const C = { paper: "#FFFFFF", terra: "#B3542F", terraSoft: "#F6E1D5", amber: "#C98A1B", amberSoft: "#FBEFD6",
    teal: "#2F7D6D", tealSoft: "#DCEFE9", red: "#B8412F", grey: "#9A8F86", line: "#E8DDD2", blue: "#4F7CAC", blueSoft: "#E1EAF4", bar: "#DDD2C7" };
  const TAU = Math.PI * 2;

  // ---------- tiện ích thời gian ----------
  const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
  const lerp = (a, b, u) => a + (b - a) * u;
  const prog = (t, a, d) => clamp((t - a) / d);
  const eo = (u) => 1 - Math.pow(1 - u, 3);
  const eio = (u) => (u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2);
  const back = (u) => { const c1 = 1.9, c3 = c1 + 1; return 1 + c3 * Math.pow(u - 1, 3) + c1 * Math.pow(u - 1, 2); };
  const pop = (t, t0, d = 0.45) => { const u = prog(t, t0, d); return u <= 0 ? 0 : back(u); };
  const tf = (g, x, y, s = 1, r = 0) => g.setAttribute("transform", `translate(${x.toFixed(1)},${y.toFixed(1)}) rotate(${r.toFixed(2)}) scale(${Math.max(0, s).toFixed(4)})`);
  const op = (g, o) => { g.setAttribute("opacity", clamp(o).toFixed(3)); g.style.display = o <= 0.001 ? "none" : ""; };
  const txt = (parent, s, a) => { const n = el("text", { "text-anchor": "middle", fill: INK, ...a }, parent); n.textContent = s; return n; };

  // ---------- nhân vật ----------
  let seed = 1;
  function person(parent, o) {
    const g = el("g", {}, parent);
    let head;
    const fig = createFigure(g, {
      drawHead: (hg) => { head = H.drawHead(hg, o); },
      drawBadge: (bg) => H.badge(bg, (o.badge || [C.terra])[0], (o.badge || [0, "circle"])[1]),
    });
    return {
      g, fig, head, off: (seed++ * 0.83) % 3, x: 0, y: 0, s: 1, face: 1,
      place(x, y, s, face) {
        this.x = x; this.y = y; this.s = s; this.face = face;
        g.setAttribute("transform", `translate(${x.toFixed(1)},${y.toFixed(1)}) scale(${(s * face).toFixed(3)},${s.toFixed(3)})`);
      },
      pose(p) { poseFigure(fig, p); },
      expr(n) { head.set(n); },
      blink(t) { head.blink(t, this.off); },
      world(pt) { return [this.x + this.face * this.s * pt[0], this.y + this.s * pt[1]]; },
      top() { const h = this.world(fig.headCenter || [0, -96]); return [h[0], h[1] - 52 * this.s]; },
    };
  }
  const hipY = (s, ground) => ground - 84 * s;

  // tư thế
  function stand(t, o = {}) {
    const w = Math.sin(TAU * 0.45 * t + (o.ph || 0));
    return { hip: [0, 0], lean: o.lean || 0, legs: [[7, 3], [-7, -3]],
      arms: [[14 + 3 * w, 6 + 4 * w], [-14 - 3 * w, -6 - 4 * w]], headTilt: (o.tilt || 0) + 2 * w };
  }
  function shrug(t, u, o = {}) {
    const p = stand(t, o), b = 4 * Math.sin(TAU * 1.2 * t) * u;
    p.arms = [[lerp(14, 86, u), lerp(6, 134, u) + b], [lerp(-14, -86, u), lerp(-6, -134, u) - b]];
    p.headTilt = (o.tilt || 0) + lerp(0, -7, u);
    return p;
  }
  function cheer(t, u, ph = 0) {
    const w = Math.sin(TAU * 1.5 * t + ph), p = stand(t, { ph });
    p.arms = [[lerp(14, 100 + 5 * w, u), lerp(6, 118 + 12 * w, u)], [lerp(-14, -100 - 5 * w, u), lerp(-6, -118 - 12 * w, u)]];
    p.hip = [0, -6 * u * Math.abs(Math.sin(TAU * 0.75 * t + ph))];
    return p;
  }
  function thumbs(t, u) { const p = stand(t); p.arms[0] = [lerp(14, 40, u), lerp(6, 95, u)]; p.lean = -3 * u; return p; }
  function walk(t, hz = 1.7) {
    const q = TAU * hz * t;
    const leg = (a) => { const th = 4 + 22 * Math.sin(a); const fl = 6 + 28 * (0.5 - 0.5 * Math.sin(a + 0.9)); return [th, th - fl]; };
    const sw = 24 * Math.sin(q);
    return { hip: [0, -3 * Math.abs(Math.cos(q))], lean: 4, legs: [leg(q), leg(q + Math.PI)],
      arms: [[4 - sw, 30 - sw], [4 + sw, 30 + sw]], headTilt: 0 };
  }
  function toss(t, u) { // tay trước vung ra phía trước như đang ném
    const p = stand(t), w = Math.sin(TAU * 1.8 * t);
    p.arms[0] = [lerp(14, 60 + 40 * w, u), lerp(6, 110 + 40 * w, u)];
    p.lean = 6 * u;
    return p;
  }

  // ---------- đồ vật ----------
  function fileCard(parent, o) {
    const g = el("g", {}, parent), w = o.w || 190, h = o.h || 240, col = o.color || C.terra;
    el("rect", { x: -w / 2 + 8, y: -h / 2 + 10, width: w, height: h, rx: 14, fill: "#000", opacity: 0.06 }, g);
    el("path", { d: `M${-w / 2},${-h / 2 + 14} q0,-14 14,-14 L${w / 2 - 42},${-h / 2} L${w / 2},${-h / 2 + 42} L${w / 2},${h / 2 - 14} q0,14 -14,14 L${-w / 2 + 14},${h / 2} q-14,0 -14,-14 Z`,
      fill: "#fff", stroke: INK, "stroke-width": 5, "stroke-linejoin": "round" }, g);
    el("path", { d: `M${w / 2 - 42},${-h / 2} L${w / 2 - 42},${-h / 2 + 42} L${w / 2},${-h / 2 + 42} Z`, fill: C.line, stroke: INK, "stroke-width": 5, "stroke-linejoin": "round" }, g);
    el("rect", { x: -w / 2 + 16, y: -h / 2 + 22, width: Math.max(w * 0.34, w - 92), height: w < 120 ? 14 : 20, rx: 6, fill: col }, g);
    const n = o.lines || Math.floor((h - 90) / 30);
    for (let i = 0; i < n; i++) el("rect", { x: -w / 2 + 22, y: -h / 2 + 66 + i * 30, width: (w - 44) * (i % 3 === 2 ? 0.6 : 0.92), height: 10, rx: 5, fill: C.bar }, g);
    if (o.label) txt(g, o.label, { x: 0, y: h / 2 + 44, "font-size": o.fs || 22, "font-weight": 600 });
    return g;
  }

  function bubble(parent, o) {
    const g = el("g", {}, parent), w = o.w || 84, h = o.h || 78, fill = o.fill || "#fff";
    const sw = { stroke: INK, "stroke-width": 4.5, "stroke-linejoin": "round" };
    el("rect", { x: -w / 2, y: -h / 2, width: w, height: h, rx: Math.min(h / 2, 26), fill, ...sw }, g);
    const tx = o.tail === "right" ? w / 2 - 28 : -w / 2 + 28, dir = o.tail === "right" ? 12 : -12;
    el("path", { d: `M${tx - 11},${h / 2 - 2} L${tx + dir},${h / 2 + 22} L${tx + 11},${h / 2 - 2}`, fill, ...sw }, g);
    el("rect", { x: tx - 9, y: h / 2 - 8, width: 18, height: 9, fill }, g);
    const inner = el("g", {}, g);
    if (o.text !== undefined) txt(inner, o.text, { y: (o.fs || 44) * 0.36, "font-size": o.fs || 44, "font-weight": 800, fill: o.color || INK });
    return { g, inner };
  }

  function shape(parent, kind, color, r = 16) {
    if (kind === "square") return el("rect", { x: -r, y: -r, width: 2 * r, height: 2 * r, rx: 4, fill: color }, parent);
    if (kind === "tri") return el("polygon", { points: `0,${-r * 1.1} ${r * 1.05},${r * 0.8} ${-r * 1.05},${r * 0.8}`, fill: color }, parent);
    if (kind === "diamond") return el("rect", { x: -r * 0.8, y: -r * 0.8, width: r * 1.6, height: r * 1.6, rx: 3, fill: color, transform: "rotate(45)" }, parent);
    if (kind === "star") {
      const pts = [];
      for (let i = 0; i < 10; i++) { const rr = i % 2 ? r * 0.45 : r * 1.05, a = (i * 36 - 90) * Math.PI / 180; pts.push(`${(rr * Math.cos(a)).toFixed(1)},${(rr * Math.sin(a)).toFixed(1)}`); }
      return el("polygon", { points: pts.join(" "), fill: color }, parent);
    }
    return el("circle", { r, fill: color }, parent);
  }

  function checkIcon(parent, r = 24, col = C.teal) {
    const g = el("g", {}, parent);
    el("circle", { r, fill: col, stroke: INK, "stroke-width": 4 }, g);
    el("path", { d: `M${-r * 0.45},${r * 0.02} L${-r * 0.1},${r * 0.36} L${r * 0.5},${-r * 0.34}`, fill: "none", stroke: "#fff", "stroke-width": r * 0.22, "stroke-linecap": "round", "stroke-linejoin": "round" }, g);
    return g;
  }

  function robot(parent) {
    const g = el("g", {}, parent);
    const ink = { stroke: INK, "stroke-width": 6, "stroke-linejoin": "round", "stroke-linecap": "round" };
    const armR = el("g", {}, g);
    el("path", { d: "M0,0 q44,14 52,70", fill: "none", ...ink, "stroke-width": 16 }, armR);
    el("circle", { cx: 52, cy: 76, r: 13, fill: "#fff", ...ink, "stroke-width": 5 }, armR);
    el("path", { d: "M-95,64 q-44,14 -52,70", fill: "none", ...ink, "stroke-width": 16 }, g);
    el("circle", { cx: -147, cy: 140, r: 13, fill: "#fff", ...ink, "stroke-width": 5 }, g);
    el("rect", { x: -95, y: 22, width: 190, height: 150, rx: 28, fill: C.terraSoft, ...ink }, g);
    txt(g, "AI", { y: 120, "font-size": 66, "font-weight": 800, fill: C.terra });
    el("rect", { x: 86, y: 58, width: 16, height: 100, rx: 6, fill: INK }, g);
    el("line", { x1: 0, y1: -150, x2: 0, y2: -196, ...ink }, g);
    const ball = el("circle", { cx: 0, cy: -206, r: 14, fill: C.terra, ...ink, "stroke-width": 5 }, g);
    el("rect", { x: -126, y: -152, width: 252, height: 174, rx: 42, fill: "#fff", ...ink }, g);
    el("rect", { x: -72, y: -168, width: 144, height: 20, rx: 8, fill: INK }, g);
    const normal = el("g", {}, g), happy = el("g", { style: "display:none" }, g);
    const pupils = el("g", {}, normal);
    [-48, 48].forEach((x) => { el("circle", { cx: x, cy: -70, r: 20, fill: INK }, pupils); el("circle", { cx: x + 6, cy: -77, r: 6, fill: "#fff" }, pupils); });
    el("path", { d: "M-40,-22 q40,26 80,0", fill: "none", ...ink }, normal);
    el("path", { d: "M-68,-64 q19,-24 38,0 M30,-64 q19,-24 38,0", fill: "none", ...ink, "stroke-width": 7 }, happy);
    el("path", { d: "M-46,-28 q46,42 92,0 z", fill: "#fff", ...ink }, happy);
    el("ellipse", { cx: -84, cy: -34, rx: 13, ry: 7, fill: "#f08f8f", opacity: 0.55 }, g);
    el("ellipse", { cx: 84, cy: -34, rx: 13, ry: 7, fill: "#f08f8f", opacity: 0.55 }, g);
    return {
      g, ball,
      face(n) { normal.style.display = n === "happy" ? "none" : ""; happy.style.display = n === "happy" ? "" : "none"; },
      look(dx) { pupils.setAttribute("transform", `translate(${dx.toFixed(1)},0)`); },
      wave(a) { armR.setAttribute("transform", `translate(95,64) rotate(${a.toFixed(1)})`); },
    };
  }

  function chip(parent, label, o = {}) {
    const g = el("g", {}, parent), w = o.w || 360, h = o.h || 70;
    el("rect", { x: 0, y: -h / 2, width: w, height: h, rx: h / 2, fill: o.fill || "#fff", stroke: INK, "stroke-width": 4.5 }, g);
    if (o.icon !== false) checkIcon(g, 20, o.iconColor || C.teal).setAttribute("transform", `translate(${h / 2},0)`);
    txt(g, label, { x: o.icon === false ? w / 2 : h - 4, y: 10, "text-anchor": o.icon === false ? "middle" : "start", "font-size": o.fs || 28, "font-weight": 700, fill: o.color || INK });
    return g;
  }

  /** Tra cứu cảnh và câu theo dòng thời gian. */
  function index(T) {
    const SC = {}; T.scenes.forEach((s) => (SC[s.id] = s));
    const L = (id, i) => SC[id].lines[i].start;
    function vis(id, t) {
      const s = SC[id];
      if (t < s.start || t > s.end) return 0;
      return Math.min(prog(t, s.start, 0.35), 1 - prog(t, s.end - 0.3, 0.3));
    }
    return { SC, L, vis };
  }

  /** Dựng window.renderAt. subField là trường phụ đề dùng cho bản này, sub cho bản ngang, subV cho bản dọc. */
  const CARD = {
    intro: ["Chia sẻ nội bộ", "Trước khi nói chuyện AI", "Vì sao tài liệu, quy trình và con người phải đi trước"],
    outro: ["Chia sẻ nội bộ", "Chuẩn hóa trước, AI đến sau", "Tài liệu rõ ràng · Quy trình được viết ra · Con người cùng hiểu"],
  };
  function direct({ T, G, R, base, vis, subField = "sub", ruleW = 160, card: cardText = CARD }) {
  const card = document.getElementById("card"), cardK = document.getElementById("cardK"), cardH = document.getElementById("cardH");
  const cardRule = document.getElementById("cardRule"), cardP = document.getElementById("cardP");
  const kicker = document.getElementById("kicker"), kickerText = document.getElementById("kickerText");
  const subBox = document.getElementById("subBox");
  let subKey = null, kickKey = null, cardKey = null;
  const allLines = []; T.scenes.forEach((s) => s.lines.forEach((l) => allLines.push(l)));

  function setCard(key, k, h, p) {
    if (cardKey === key) return;
    cardK.textContent = k; cardH.textContent = h; cardP.textContent = p; cardKey = key;
  }

  window.renderAt = function (t) {
    // thẻ mở đầu và kết thúc
    const introO = t < T.intro ? Math.min(prog(t, 0.1, 0.5), 1 - prog(t, T.intro - 0.4, 0.4)) : 0;
    const outroO = t >= T.outroStart ? prog(t, T.outroStart, 0.5) : 0;
    if (t < T.intro) setCard("intro", ...cardText.intro);
    else setCard("outro", ...cardText.outro);
    const co = Math.max(introO, outroO);
    card.style.opacity = co.toFixed(3);
    card.style.transform = `translateY(${((1 - co) * 16).toFixed(1)}px)`;
    const ru = t < T.intro ? eo(prog(t, 0.6, 0.8)) : eo(prog(t, T.outroStart + 0.4, 0.8));
    cardRule.style.width = (ru * ruleW).toFixed(1) + "px";
    op(base, t > T.intro && t < T.outroStart ? Math.min(prog(t, T.intro, 0.4), 1 - prog(t, T.outroStart - 0.4, 0.4)) : 0);

    // các cảnh
    let kick = null, kickO = 0;
    T.scenes.forEach((s) => {
      const o = vis(s.id, t);
      op(G[s.id], o);
      if (o > 0) { R[s.id](t); if (o > kickO) { kickO = o; kick = s.kicker; } }
    });
    if (kick !== kickKey) { kickerText.textContent = kick || ""; kickKey = kick; }
    kicker.style.opacity = kickO.toFixed(3);

    // phụ đề
    const ln = allLines.find((l) => t >= l.start - 0.08 && t <= l.end + 0.1);
    if (ln) {
      if (subKey !== ln.start) { subBox.innerHTML = ln[subField].map((x) => `<span>${x}</span>`).join(""); subKey = ln.start; }
      subBox.style.opacity = Math.min(prog(t, ln.start - 0.08, 0.12), 1 - prog(t, ln.end - 0.02, 0.12)).toFixed(3);
      subBox.style.display = "";
    } else { subBox.style.display = "none"; }
  };


    window.VIDEO = { total: T.total, fps: 30 };
    window.renderAt(0);
  }

  window.Lib = { C, TAU, INK, clamp, lerp, prog, eo, eio, back, pop, tf, op, txt, person, hipY,
    stand, shrug, cheer, thumbs, walk, toss, fileCard, bubble, shape, checkIcon, robot, chip, index, direct };
})();
