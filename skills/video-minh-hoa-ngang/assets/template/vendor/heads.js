// Mặt cartoon tự vẽ, mở rộng từ mẫu meme-video-html: một khuôn mặt chứa nhiều biểu cảm,
// bật tắt bằng setExpr để nhân vật đổi cảm xúc giữa chừng mà không phải dựng lại.
// Mặt nhìn sang phải. Không dùng mặt người thật, không logo thương hiệu.
(function () {
  const { el } = window.StickRig;
  const INK = "#231a14";

  function drawHair(g, spec, ink) {
    const c = spec.hair;
    const styles = {
      curly: () => {
        for (let i = 0; i < 8; i++) {
          const a = (-205 + i * 22) * (Math.PI / 180);
          el("circle", { cx: 34 * Math.cos(a) - 2, cy: 34 * Math.sin(a) - 4, r: 13, fill: c, ...ink, "stroke-width": 3 }, g);
        }
      },
      short: () => el("path", { d: "M-36,-4 C-40,-38 -6,-52 22,-42 C36,-36 40,-26 38,-14 C26,-24 6,-24 -8,-18 C-18,-12 -26,-10 -36,-4 Z", fill: c, ...ink }, g),
      slick: () => el("path", { d: "M-36,2 C-42,-34 0,-50 30,-36 C40,-30 40,-22 36,-18 C18,-30 -6,-28 -20,-18 C-26,-12 -30,-6 -36,2 Z", fill: c, ...ink }, g),
      silver: () => el("path", { d: "M-36,6 C-46,-30 -14,-52 16,-44 C34,-40 42,-26 36,-16 C24,-30 4,-34 -12,-26 C-22,-20 -28,-8 -36,6 Z", fill: c, ...ink }, g),
      bun: () => {
        el("circle", { cx: -22, cy: -42, r: 15, fill: c, ...ink, "stroke-width": 3 }, g);
        el("path", { d: "M-37,2 C-44,-34 -4,-50 24,-40 C38,-34 40,-24 37,-15 C22,-26 2,-28 -14,-20 C-24,-14 -30,-6 -37,2 Z", fill: c, ...ink }, g);
      },
      long: () => el("path", { d: "M-38,30 C-50,-20 -16,-52 18,-44 C36,-38 42,-26 37,-15 C22,-28 0,-30 -14,-20 C-22,-8 -24,12 -20,34 C-26,38 -34,36 -38,30 Z", fill: c, ...ink }, g),
    };
    styles[spec.hairStyle]();
  }

  const EXPR = {
    smile: (g, ink) => {
      const e = el("g", { class: "eyes" }, g);
      [9, 26].forEach((x) => el("ellipse", { cx: x, cy: -4, rx: 3.6, ry: 4.8, fill: INK }, e));
      el("path", { d: "M8,15 q10,9 20,0", fill: "none", ...ink, "stroke-width": 3 }, g);
      return e;
    },
    grin: (g, ink) => {
      const e = el("g", { class: "eyes" }, g);
      [9, 26].forEach((x) => el("ellipse", { cx: x, cy: -4, rx: 3.6, ry: 4.8, fill: INK }, e));
      el("path", { d: "M5,13 q13,14 28,0 z", fill: "#fff", ...ink, "stroke-width": 3 }, g);
      return e;
    },
    happy: (g, ink) => {
      const e = el("g", { class: "eyes" }, g);
      el("path", { d: "M3,-2 q6,-8 12,0 M20,-2 q6,-8 12,0", fill: "none", ...ink, "stroke-width": 3.5 }, e);
      el("path", { d: "M5,12 q13,15 28,0 z", fill: "#fff", ...ink, "stroke-width": 3 }, g);
      return e;
    },
    worried: (g, ink) => {
      const e = el("g", { class: "eyes" }, g);
      [9, 26].forEach((x) => el("ellipse", { cx: x, cy: -3, rx: 3.6, ry: 4.8, fill: INK }, e));
      el("path", { d: "M2,-16 l11,4 M33,-16 l-10,4", fill: "none", ...ink, "stroke-width": 3 }, g);
      el("path", { d: "M8,20 q5,-5 10,0 q5,5 10,0", fill: "none", ...ink, "stroke-width": 3 }, g);
      return e;
    },
    shocked: (g, ink) => {
      const e = el("g", { class: "eyes" }, g);
      [8, 26].forEach((x) => {
        el("circle", { cx: x, cy: -4, r: 8, fill: "#fff", ...ink, "stroke-width": 3 }, e);
        el("circle", { cx: x + 2, cy: -4, r: 3, fill: INK }, e);
      });
      el("ellipse", { cx: 18, cy: 20, rx: 6, ry: 8, fill: "#6b1f1f", ...ink, "stroke-width": 3 }, g);
      return e;
    },
    think: (g, ink) => {
      const e = el("g", { class: "eyes" }, g);
      [11, 28].forEach((x) => el("ellipse", { cx: x, cy: -7, rx: 3.6, ry: 4.8, fill: INK }, e));
      el("path", { d: "M10,18 l15,-2", fill: "none", ...ink, "stroke-width": 3 }, g);
      return e;
    },
  };

  /** spec: { skin, hair, hairStyle, glasses, exprs:[...] } ; trả về { set(name), blink(t, off) } */
  function drawHead(g, spec) {
    const ink = { stroke: INK, "stroke-width": 4, "stroke-linecap": "round", "stroke-linejoin": "round" };
    el("ellipse", { cx: -30, cy: 4, rx: 8, ry: 10, fill: spec.skin, ...ink }, g);
    el("ellipse", { cx: 0, cy: 0, rx: 36, ry: 40, fill: spec.skin, ...ink }, g);
    drawHair(g, spec, ink);
    const groups = {};
    (spec.exprs || ["smile"]).forEach((name) => {
      const eg = el("g", { style: "display:none" }, g);
      groups[name] = { g: eg, eyes: EXPR[name](eg, ink) };
    });
    if (spec.glasses) {
      el("circle", { cx: 9, cy: -4, r: 10, fill: "none", ...ink, "stroke-width": 3 }, g);
      el("circle", { cx: 29, cy: -4, r: 10, fill: "none", ...ink, "stroke-width": 3 }, g);
      el("path", { d: "M-1,-6 L-24,-2", fill: "none", ...ink, "stroke-width": 3 }, g);
    }
    el("ellipse", { cx: 30, cy: 10, rx: 6, ry: 3.5, fill: "#f08f8f", opacity: 0.5 }, g);
    let current = null;
    const api = {
      set(name) {
        if (name === current) return;
        Object.keys(groups).forEach((k) => (groups[k].g.style.display = k === name ? "" : "none"));
        current = name;
      },
      blink(t, off) {
        if (!current) return;
        const u = (t + off) % 3.1;
        const sy = u < 0.12 ? 0.15 : 1;
        groups[current].eyes.setAttribute("transform", `translate(0,-4) scale(1,${sy}) translate(0,4)`);
      },
    };
    api.set((spec.exprs || ["smile"])[0]);
    return api;
  }

  /** Huy hiệu áo chỉ là hình màu đơn giản. */
  function badge(g, color, shape) {
    if (shape === "star") {
      const pts = [];
      for (let i = 0; i < 10; i++) {
        const r = i % 2 ? 6 : 14, a = (i * 36 - 90) * (Math.PI / 180);
        pts.push(`${(r * Math.cos(a)).toFixed(1)},${(r * Math.sin(a)).toFixed(1)}`);
      }
      el("polygon", { points: pts.join(" "), fill: color }, g);
    } else if (shape === "square") {
      el("rect", { x: -11, y: -11, width: 22, height: 22, rx: 4, fill: color }, g);
    } else if (shape === "diamond") {
      el("rect", { x: -10, y: -10, width: 20, height: 20, rx: 3, fill: color, transform: "rotate(45)" }, g);
    } else {
      el("circle", { r: 12, fill: color }, g);
    }
  }

  window.Heads = { drawHead, badge, INK };
})();
