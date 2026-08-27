"use client";

import { useEffect, useRef } from "react";

const COLOURS = ["#ffc845", "#3ddce8", "#8fe04a", "#ff7a5c"];

/**
 * A single burst on a canvas, fired once when `fire` flips true.
 *
 * Canvas rather than a few hundred DOM nodes, and it tears itself down when
 * the last particle leaves the frame so nothing keeps painting afterwards.
 * Skipped entirely under reduced motion.
 */
export function Confetti({ fire }: { fire: boolean }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (!fire) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    if (window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) return;

    const context = canvas.getContext("2d");
    if (!context) return;

    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const width = canvas.offsetWidth;
    const height = canvas.offsetHeight;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    context.scale(dpr, dpr);

    const particles = Array.from({ length: 70 }, () => {
      const angle = -Math.PI / 2 + (Math.random() - 0.5) * 1.9;
      const speed = 5 + Math.random() * 7;
      return {
        x: width / 2,
        y: height * 0.45,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed,
        size: 4 + Math.random() * 5,
        spin: (Math.random() - 0.5) * 0.3,
        rotation: Math.random() * Math.PI,
        colour: COLOURS[Math.floor(Math.random() * COLOURS.length)],
        life: 1,
      };
    });

    let frame = 0;
    const tick = () => {
      context.clearRect(0, 0, width, height);
      let alive = false;

      for (const p of particles) {
        p.vy += 0.32;
        p.vx *= 0.99;
        p.x += p.vx;
        p.y += p.vy;
        p.rotation += p.spin;
        p.life -= 0.011;

        if (p.life > 0 && p.y < height + 40) {
          alive = true;
          context.save();
          context.translate(p.x, p.y);
          context.rotate(p.rotation);
          context.globalAlpha = Math.max(0, p.life);
          context.fillStyle = p.colour;
          context.fillRect(-p.size / 2, -p.size / 2, p.size, p.size * 0.6);
          context.restore();
        }
      }

      if (alive) frame = requestAnimationFrame(tick);
      else context.clearRect(0, 0, width, height);
    };

    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [fire]);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden
      className="pointer-events-none absolute inset-0 h-full w-full"
    />
  );
}
