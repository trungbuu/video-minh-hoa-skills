// Stick-figure rig: builds SVG figures once, then poses them as a pure function of time.
// Angle convention everywhere: 0deg = pointing straight down, positive = rotating toward +x (forward).
(function () {
  const NS = "http://www.w3.org/2000/svg";
  const RAD = Math.PI / 180;

  function el(tag, attrs, parent) {
    const node = document.createElementNS(NS, tag);
    for (const k in attrs) node.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(node);
    return node;
  }

  function polar(p, len, ang) {
    return [p[0] + len * Math.sin(ang * RAD), p[1] + len * Math.cos(ang * RAD)];
  }

  // Rubber-hose limb: quadratic curve forced through the middle joint, plus a short end stub (foot).
  function limbPath(a, b, c, stub) {
    const ctrl = [2 * b[0] - (a[0] + c[0]) / 2, 2 * b[1] - (a[1] + c[1]) / 2];
    let d = `M${a[0].toFixed(1)},${a[1].toFixed(1)} Q${ctrl[0].toFixed(1)},${ctrl[1].toFixed(1)} ${c[0].toFixed(1)},${c[1].toFixed(1)}`;
    if (stub) d += ` L${stub[0].toFixed(1)},${stub[1].toFixed(1)}`;
    return d;
  }

  // Body proportions in figure-local units (scaled per character by the parent transform).
  const DIM = { torso: 62, torsoW: 50, thigh: 42, shin: 42, upper: 30, fore: 28, limbW: 15, outline: 5, foot: 13 };

  /**
   * Create a figure inside `parent`. Returns handles used by `poseFigure`.
   * `drawHead(group)` and `drawBadge(group)` paint the character-specific art in local coords.
   */
  function createFigure(parent, { drawHead, drawBadge }) {
    const root = el("g", {}, parent);
    const parts = {};
    const base = { fill: "none", "stroke-linecap": "round", "stroke-linejoin": "round" };
    // Draw order: back limbs, torso, front limbs, so the far arm/leg tucks behind the shirt.
    // Each part = black outline stroke with a narrower white stroke on top.
    ["legB", "armB", "torso", "legA", "armA"].forEach((name) => {
      const w = name === "torso" ? DIM.torsoW : DIM.limbW;
      parts[name] = [
        el("path", { ...base, stroke: "#1b1b1b", "stroke-width": w + DIM.outline * 2 }, root),
        el("path", { ...base, stroke: "#ffffff", "stroke-width": w }, root),
      ];
    });
    const badge = el("g", {}, root);
    drawBadge(badge);
    const head = el("g", {}, root);
    const headArt = el("g", {}, head);
    drawHead(headArt);
    return { root, parts, badge, head, headArt };
  }

  function setPath(pair, d) {
    pair[0].setAttribute("d", d);
    pair[1].setAttribute("d", d);
  }

  /**
   * Pose a figure. pose = { hip:[x,y], lean, legs:[[thigh,shin],[thigh,shin]], arms:[[upper,fore],[upper,fore]], headTilt, headScale }
   * Leg/arm angles are absolute (already include lean where wanted).
   */
  function poseFigure(fig, pose) {
    const hip = pose.hip;
    const up = 180 + pose.lean; // torso direction points up, tilted forward by lean
    const neck = polar(hip, DIM.torso, up);
    const shoulder = polar(hip, DIM.torso * 0.82, up);
    setPath(fig.parts.torso, `M${hip[0].toFixed(1)},${hip[1].toFixed(1)} L${neck[0].toFixed(1)},${neck[1].toFixed(1)}`);

    ["legA", "legB"].forEach((name, i) => {
      const [th, sh] = pose.legs[i];
      const knee = polar(hip, DIM.thigh, th);
      const ankle = polar(knee, DIM.shin, sh);
      setPath(fig.parts[name], limbPath(hip, knee, ankle, polar(ankle, DIM.foot, sh + 95)));
    });
    ["armA", "armB"].forEach((name, i) => {
      const [ua, fa] = pose.arms[i];
      const elbow = polar(shoulder, DIM.upper, ua);
      const hand = polar(elbow, DIM.fore, fa);
      setPath(fig.parts[name], limbPath(shoulder, elbow, hand));
      fig[name + "Hand"] = hand;
    });

    const mid = polar(hip, DIM.torso * 0.5, up);
    fig.badge.setAttribute("transform", `translate(${mid[0].toFixed(1)},${mid[1].toFixed(1)}) rotate(${pose.lean.toFixed(1)})`);
    const headC = polar(neck, 34, up);
    const hs = 1.22 * (pose.headScale || 1);
    fig.head.setAttribute("transform", `translate(${headC[0].toFixed(1)},${headC[1].toFixed(1)}) rotate(${(pose.headTilt || 0).toFixed(1)}) scale(${hs})`);
    fig.headCenter = headC;
  }

  /** Classic run cycle; phase p in radians. Returns a pose around hip (0, 0). */
  function runPose(p, { lean = 18, stride = 48, bob = 8 } = {}) {
    const leg = (q) => {
      const thigh = 8 + stride * Math.sin(q);
      const flex = 18 + 80 * (0.5 - 0.5 * Math.sin(q + 0.9)); // back leg kicks up hard
      return [thigh, thigh - flex];
    };
    const arm = (q) => {
      const upper = lean - 48 * Math.sin(q);
      return [upper, upper + 85];
    };
    return {
      hip: [0, -bob * Math.abs(Math.cos(p))],
      lean,
      legs: [leg(p), leg(p + Math.PI)],
      arms: [arm(p), arm(p + Math.PI)],
      headTilt: 3 * Math.sin(2 * p),
    };
  }

  window.StickRig = { el, polar, createFigure, poseFigure, runPose, DIM };
})();
