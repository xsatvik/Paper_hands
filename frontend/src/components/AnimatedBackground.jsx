import { useEffect, useRef } from "react";

const TOKENS = [
  "-94%", "REKT", "▼", "-47%", "RUG", "NGMI",
  "$0.00", "-100%", "PAPER", "HANDS", "-68%", "REKT",
  "SOLD", "-82%", "EXIT LIQ", "-99%", "▼▼", "REKT",
  "-34%", "GM?", "REKT", "-55%", "TOP", "BOUGHT",
  "-71%", "APES", "REKT", "HOLD?", "-88%", "REKT",
];

// Covalent green, hot pink, cyan, red
const COLORS = [
  [120, 255, 50],   // lime green
  [255, 95, 158],   // hot pink
  [77, 219, 200],   // cyan/teal
  [220, 50, 20],    // red
  [120, 255, 50],   // lime green weighted heavier
];

const CHAR_H = 22;
const COL_W  = 38;

function makeStream(x, canvasH, immediate = false) {
  const length = 5 + Math.floor(Math.random() * 12);
  const color  = COLORS[Math.floor(Math.random() * COLORS.length)];
  return {
    x,
    y: immediate
      ? -CHAR_H * length + Math.random() * (canvasH + CHAR_H * length)
      : -(CHAR_H * length) - Math.random() * 800,
    speed:      0.5 + Math.random() * 1.4,
    length,
    chars:      Array.from({ length }, () => TOKENS[Math.floor(Math.random() * TOKENS.length)]),
    brightness: 0.28 + Math.random() * 0.42,
    color,
  };
}

export default function AnimatedBackground() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx    = canvas.getContext("2d");
    let raf;
    let streams  = [];

    function resize() {
      canvas.width  = window.innerWidth;
      canvas.height = window.innerHeight;
      const numCols = Math.ceil(canvas.width / COL_W);
      streams = Array.from({ length: numCols }, (_, i) =>
        makeStream(i * COL_W + COL_W / 2, canvas.height, true)
      );
    }

    resize();
    window.addEventListener("resize", resize);

    function draw() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.font      = `10px "Courier New", monospace`;
      ctx.textAlign = "center";

      for (const s of streams) {
        const [r, g, b] = s.color;

        for (let i = 0; i < s.chars.length; i++) {
          const cy = s.y - i * CHAR_H;
          if (cy < -CHAR_H || cy > canvas.height + CHAR_H) continue;

          const t     = 1 - i / s.chars.length;
          const alpha = t * t * s.brightness;

          if (i === 0) {
            // Head char: boosted, lighter
            const rr = Math.min(r + 80, 255);
            const gg = Math.min(g + 60, 255);
            const bb = Math.min(b + 40, 255);
            ctx.fillStyle = `rgba(${rr},${gg},${bb},${Math.min(alpha * 1.8, 0.95)})`;
          } else {
            ctx.fillStyle = `rgba(${r},${g},${b},${alpha})`;
          }

          ctx.fillText(s.chars[i], s.x, cy);
        }

        s.y += s.speed;

        if (s.y - s.length * CHAR_H > canvas.height) {
          const len   = 5 + Math.floor(Math.random() * 12);
          s.y         = -(CHAR_H * len) - Math.random() * 300;
          s.speed     = 0.5 + Math.random() * 1.4;
          s.length    = len;
          s.chars     = Array.from({ length: len }, () => TOKENS[Math.floor(Math.random() * TOKENS.length)]);
          s.brightness = 0.28 + Math.random() * 0.42;
          s.color     = COLORS[Math.floor(Math.random() * COLORS.length)];
        }
      }

      raf = requestAnimationFrame(draw);
    }

    draw();
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", resize);
    };
  }, []);

  return <canvas ref={canvasRef} className="bg-canvas" />;
}
