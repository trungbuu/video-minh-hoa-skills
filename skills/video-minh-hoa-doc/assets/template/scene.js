// Scene kit của template kể chuyện: dựng cảnh từ mục "scenes" trong script.json, không cần viết code.
// Sáu kiểu cảnh: hook, list, point, quiz, stat, cta. Mọi mốc nhận neo {line, word} hoặc {scene, at} hoặc {abs}.
// Muốn chuyển động riêng thì viết scene.js mới trên cùng engine vendor/story.js (xem motion-video-full).
(function () {
  const { el } = window.StickRig;
  const L = window.Lib;
  const { clamp, lerp, prog, eo, eio, pop, tf, op, TAU } = L;
  const A = window.Story, P = A.P, SC = A.SC, BEAT = A.BEAT, CUES = A.CUES;
  const SCN = window.SCENES || [];
  const META = window.META || {};
  const GROUND = 1150;

  /** Giải neo trong cấu hình cảnh thành giây. */
  function at(x, fallback) {
    if (x == null) return fallback;
    if (typeof x === "number") return x;
    if (x.word != null) return A.W(x.line, x.word, x.nth || 1) + (x.offset || 0);
    if (x.at != null) return SC[x.scene != null ? x.scene : 0] + x.at + (x.offset || 0);
    if (x.abs != null) return x.abs;
    return fallback;
  }

  const svg = document.getElementById("stage");
  const { glow, wm, cam } = A.stageBase(svg);
  const SPEC = { coach: A.COACH, coach2: A.COACH2, client: A.CLIENT };

  // ---------- đạo cụ ----------
  const PROPS = {
    bulb(g) {
      const b = el("g", {}, g);
      el("circle", { r: 70, fill: "url(#glow)" }, b);
      el("path", { d: "M-30,10 C-52,-14 -40,-58 0,-58 C40,-58 52,-14 30,10 L22,30 L-22,30 Z", fill: "#FFF4E8", stroke: "#1b1b1b", "stroke-width": 5, "stroke-linejoin": "round" }, b);
      el("rect", { x: -20, y: 32, width: 40, height: 18, rx: 5, fill: P.ink }, b);
      el("path", { d: "M-10,8 L-4,-18 L4,-4 L10,-24", fill: "none", stroke: P.red, "stroke-width": 5, "stroke-linecap": "round" }, b);
      return { g: b, draw(t, t0) { tf(b, 760, 860 - 8 * Math.sin(TAU * t / (2 * BEAT)), 1.6 * pop(t, t0, 0.5)); } };
    },
    chart(g) {
      const c = el("g", { filter: "url(#soft)" }, g);
      el("rect", { x: -170, y: -200, width: 340, height: 380, rx: 22, fill: "#fff", stroke: P.decor, "stroke-width": 3 }, c);
      const bars = [0, 1, 2, 3, 4].map((i) => el("rect", { x: -130 + i * 56, width: 38, rx: 6, fill: i === 4 ? "url(#vit)" : P.decor }, c));
      return { g: c, draw(t, t0) {
        tf(c, 760, 900, pop(t, t0, 0.55));
        bars.forEach((r, i) => { const h = [70, 110, 90, 150, 230][i] * eo(prog(t, t0 + 0.3 + i * BEAT / 2, 0.5)); r.setAttribute("y", (150 - h).toFixed(1)); r.setAttribute("height", h.toFixed(1)); });
      } };
    },
    plant(g) {
      const p = el("g", {}, g);
      const stem = el("path", { fill: "none", stroke: P.olive, "stroke-width": 10, "stroke-linecap": "round" }, p);
      const leaves = [0, 1, 2, 3].map((i) => el("path", { d: "M0,0 C18,-30 58,-34 78,-12 C54,8 20,12 0,0 Z", fill: i % 2 ? P.olive : "#9DB07A" }, p));
      el("path", { d: "M-70,0 L70,0 L52,64 L-52,64 Z", fill: P.soft, stroke: P.ink, "stroke-width": 5 }, p);
      return { g: p, draw(t, t0) {
        tf(p, 780, GROUND - 64, 1); const gr = eo(prog(t, t0, 2.4));
        stem.setAttribute("d", `M0,0 C-10,${(-80 * gr).toFixed(1)} 16,${(-160 * gr).toFixed(1)} 0,${(-250 * gr).toFixed(1)}`);
        leaves.forEach((lf, i) => { const side = i % 2 ? -1 : 1, u = eo(prog(t, t0 + 0.4 + i * 0.4, 0.6));
          lf.setAttribute("transform", `translate(0,${((-60 - i * 50) * gr).toFixed(1)}) scale(${(side * u).toFixed(3)},${u.toFixed(3)})`); });
      } };
    },
    check(g) {
      const c = L.checkIcon(g, 64, P.red);
      return { g: c, draw(t, t0) { tf(c, 780, 860, pop(t, t0, 0.5)); } };
    },
    clipboard(g) {
      const c = A.clipboard(g);
      return { g: c, draw(t, t0) { tf(c, 780, 880, 2.2 * pop(t, t0, 0.5), -6); } };
    },
    none() { return { g: null, draw() {} }; },
  };

  // ---------- dựng từng cảnh ----------
  const G = SC.map(() => el("g", {}, cam));
  const R = SCN.map((cfg, k) => {
    const g = G[k]; const type = cfg.type || "point"; const t0 = SC[k];
    if (type === "hook") {
      A.ground(g, 260, 820);
      const c = A.person(g, SPEC[cfg.figure || "coach"]), cb = A.clipboard(g);
      const q = L.bubble(g, { w: 96, h: 90, text: cfg.bubble || "?", fs: 64, color: P.red });
      return (t) => {
        const lt = t - t0, look = Math.floor(Math.max(0, lt - 0.6) / (2 * BEAT)) % 2 ? -1 : 1;
        c.place(540, GROUND - 84 * 1.7, 1.7 * pop(t, t0 + 0.05, 0.5) || 0.001, look);
        c.pose(A.holdItem(t)); A.talk(c, t, t0, SC[k + 1] || A.DUR, lt > 3 ? "happy" : "think"); c.blink(t);
        const hand = c.world(c.fig.armAHand || [40, 0]); tf(cb, hand[0] + 8 * look, hand[1] - 20, 1.25 * pop(t, t0 + 0.2, 0.5));
        const hd = c.top(); tf(q.g, hd[0] + 110, hd[1] - 30 + 6 * Math.sin(TAU * t), pop(t, t0 + 0.9, 0.5));
      };
    }
    if (type === "list") {
      const items = cfg.items || [];
      const rows = items.map(([ch, name]) => {
        const r = el("g", {}, g);
        el("rect", { x: 0, y: -70, width: 780, height: 88, rx: 12, fill: P.soft }, r);
        el("rect", { x: 0, y: 14, width: 780, height: 4, fill: P.red, opacity: 0.8 }, r);
        const l = el("text", { x: 62, y: 0, "text-anchor": "middle", "font-size": 92, fill: "url(#vit)" }, r); l.textContent = ch;
        const n = el("text", { x: 140, y: -8, "font-size": 58, fill: P.ink2, "font-weight": 700 }, r); n.textContent = String(name).toUpperCase();
        return r;
      });
      const start = at(cfg.itemsAt, t0 + 0.6);
      return (t) => rows.forEach((r, i) => {
        const u = prog(t, start + i * BEAT, 0.45); tf(r, 150 + 80 * (1 - eo(u)), 790 + i * 104, 1); op(r, u * 1.4);
      });
    }
    if (type === "quiz") {
      A.ground(g);
      const c = A.person(g, SPEC[cfg.figure || "coach"]), cl = A.person(g, SPEC[cfg.partner || "client"]);
      const q = L.bubble(g, { w: 110, h: 100, text: "?", fs: 70, color: P.red, tail: "left" });
      const tA = at(cfg.answer && cfg.answer.at, A.lineAt(k, 1));
      return (t) => {
        c.place(330, GROUND - 84 * 1.45, 1.45, 1); cl.place(760, GROUND - 84 * 1.45, 1.45, -1);
        const ok = t >= tA;
        c.pose(ok ? A.point(t, eo(prog(t, tA, 0.5))) : L.stand(t, { tilt: 8 })); A.talk(c, t, tA, SC[k + 1] || A.DUR, ok ? "smile" : "think"); c.blink(t);
        cl.pose(L.stand(t, { ph: 1 })); cl.expr(ok ? "happy" : cfg.clientMood || "worried"); cl.blink(t);
        const ch = cl.top(); tf(q.g, ch[0] - 60, ch[1] - 50, pop(t, t0 + 0.5, 0.45) * (1 - prog(t, tA, 0.3)));
      };
    }
    if (type === "stat") {
      const num = el("text", { x: 540, y: 960, "text-anchor": "middle", "font-size": 300, fill: "url(#vit)" }, g);
      const lab = el("text", { x: 540, y: 1060, "text-anchor": "middle", "font-size": 54, fill: P.ink2 }, g); lab.textContent = (cfg.label || "").toUpperCase();
      const a0 = at(cfg.countAt, t0 + 0.6), val = Number(cfg.value || 0);
      return (t) => {
        const u = eo(prog(t, a0, 1.4)); num.textContent = `${Math.round(val * u).toLocaleString("vi-VN")}${cfg.unit || ""}`;
        tf(num, 0, 0, 1); op(num, prog(t, a0, 0.2)); op(lab, prog(t, a0 + 0.8, 0.4));
      };
    }
    if (type === "cta") {
      A.ground(g, 170, 910);
      const team = [A.COACH, A.COACH2, A.COACH].map((s) => A.person(g, s));
      return (t) => team.forEach((p, i) => {
        p.place(300 + i * 240, GROUND + 120 - 84 * 0.9, 0.9, i === 2 ? -1 : 1);
        p.pose(L.cheer(t, eo(prog(t, t0 + 0.8, 0.5)), i)); p.expr("happy"); p.blink(t);
      });
    }
    // point
    A.ground(g);
    const c = A.person(g, SPEC[cfg.figure || "coach"]);
    const partner = cfg.partner ? A.person(g, SPEC[cfg.partner]) : null;
    const prop = (PROPS[cfg.prop || "none"] || PROPS.none)(g);
    const tAct = at(cfg.actionAt, A.lineAt(k, 1));
    return (t) => {
      const u = eo(prog(t, tAct, 0.5));
      c.place(partner ? 330 : 330, GROUND - 84 * 1.45, 1.45, 1);
      const pose = cfg.pose || "point";
      c.pose(pose === "cheer" ? L.cheer(t, u) : pose === "squat" ? A.squat(t, 0.8 * (0.5 - 0.5 * Math.cos(TAU * Math.max(0, t - tAct) / (4 * BEAT)))) :
        pose === "wave" ? A.wave(t, u) : pose === "hold" ? A.holdItem(t) : A.point(t, u));
      A.talk(c, t, t0, SC[k + 1] || A.DUR, t >= tAct ? "happy" : "smile"); c.blink(t);
      if (partner) { partner.place(760, GROUND - 84 * 1.45, 1.45, -1); partner.pose(L.stand(t, { ph: 1 })); partner.expr(t >= tAct ? "happy" : "smile"); partner.blink(t); }
      prop.draw(t, at(cfg.propAt, t0 + 0.6));
    };
  });

  const letters = META.letters || "";
  const renderText = A.makeText({
    letters,
    titles: SCN.map((c) => (c.type === "cta" ? { h: "" } : { k: c.kicker, h: c.headline, s: c.sub, big: c.big, mid: c.mid })),
    chips: SCN.map((c) => c.chips || []),
    chipAt: (sc) => at(SCN[sc] && SCN[sc].chipsAt, A.lineAt(sc, 1) + 0.2),
    answers: SCN.map((c) => (c.answer ? { text: c.answer.text, at: at(c.answer.at, A.lineAt(SCN.indexOf(c), 1)) } : null)),
    hideTitle: (sc) => SCN[sc] && SCN[sc].type === "cta",
    dots: (sc, t) => letters.split("").map((_, i) => { const d = SCN[sc] && SCN[sc].dot; return d == null ? (sc > 0 && SCN[sc].type !== "cta" && i < sc ? "on" : "") : i < d ? "on" : i === d ? "now" : ""; }),
    dotsVisible: (t) => 1 - prog(t, CUES.ending - 0.2, 0.4),
  });

  let wmKey = -1;
  function renderAt(t) {
    const bp = A.beatPulse(t), sc = A.sceneAt(t), a = SC[sc], b = A.sceneEnd(sc);
    const push = 1 + 0.018 * eio(prog(t, a, b - a));
    cam.setAttribute("transform", `translate(${(540 - 540 * push).toFixed(1)},${(960 - 960 * push).toFixed(1)}) scale(${push.toFixed(4)})`);
    glow.setAttribute("r", (600 + 30 * bp + 40 * A.hitNear(t)).toFixed(1));
    if (sc !== wmKey) { wm.textContent = (SCN[sc] && SCN[sc].wm) || ""; wmKey = sc; }
    wm.setAttribute("opacity", A.win(t, a, b, 0.5, 0.35).toFixed(3));
    wm.setAttribute("transform", `translate(${(60 * (1 - eo(prog(t, a, 1.2))) - 30 * prog(t, a, b - a)).toFixed(1)},0)`);
    G.forEach((g, k) => {
      const vv = k === sc ? A.win(t, SC[k], A.sceneEnd(k), 0.35, 0.3) : 0;
      op(g, vv);
      if (vv > 0) g.setAttribute("transform", `translate(${(50 * (1 - eo(prog(t, SC[k], 0.6)))).toFixed(1)},0)`);
    });
    if (R[sc]) R[sc](t);
    renderText(t, bp, sc);
  }
  A.finish(renderAt, "story");
})();
