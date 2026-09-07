"use client";

import { useEffect, useRef } from "react";

export default function LightRays({
  raysOrigin = "top-center",
  raysColor = "#ffffff",
  raysSpeed = 1,
  lightSpread = 1,
  rayLength = 2,
  pulsating = false,
  fadeDistance = 1,
  saturation = 1,
  followMouse = true,
  mouseInfluence = 0.1,
  noiseAmount = 0,
  distortion = 0,
}) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animationFrameId;
    let width = 0;
    let height = 0;

    let mouseX = 0;
    let mouseY = 0;
    let targetMouseX = 0;
    let targetMouseY = 0;

    const resize = () => {
      if (!canvas.parentElement) return;
      const rect = canvas.parentElement.getBoundingClientRect();
      width = rect.width;
      height = rect.height;
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

      targetMouseX = width / 2;
      targetMouseY = height / 3;
      mouseX = targetMouseX;
      mouseY = targetMouseY;
    };

    resize();
    window.addEventListener("resize", resize);

    const onMouseMove = (e) => {
      if (!followMouse || !canvas) return;
      const rect = canvas.getBoundingClientRect();
      targetMouseX = e.clientX - rect.left;
      targetMouseY = e.clientY - rect.top;
    };

    window.addEventListener("mousemove", onMouseMove);

    // Number of volumetric rays
    const rayCount = 18;
    const rays = [];
    for (let i = 0; i < rayCount; i++) {
      rays.push({
        baseAngle: ((i / rayCount) - 0.5) * Math.PI * 0.85 * lightSpread,
        width: 0.05 + Math.random() * 0.09 * lightSpread,
        speed: (0.4 + Math.random() * 0.8) * raysSpeed,
        phase: Math.random() * Math.PI * 2,
        alpha: 0.12 + Math.random() * 0.22,
        lengthMult: 0.8 + Math.random() * 0.5,
      });
    }

    let startTime = performance.now();

    const render = (currentTime) => {
      const elapsed = (currentTime - startTime) * 0.001;

      // Smooth mouse easing
      mouseX += (targetMouseX - mouseX) * 0.05;
      mouseY += (targetMouseY - mouseY) * 0.05;

      ctx.clearRect(0, 0, width, height);

      // Determine ray origin point
      let originX = width / 2;
      let originY = 0;

      if (raysOrigin === "top-left") {
        originX = 0;
        originY = 0;
      } else if (raysOrigin === "top-right") {
        originX = width;
        originY = 0;
      } else if (raysOrigin === "center") {
        originX = width / 2;
        originY = height / 2;
      }

      if (followMouse) {
        originX += (mouseX - width / 2) * mouseInfluence;
        originY += (mouseY - height / 2) * (mouseInfluence * 0.4);
      }

      ctx.save();
      ctx.globalCompositeOperation = "screen";

      const maxRadius = Math.max(width, height) * rayLength;

      rays.forEach((ray) => {
        const sway = Math.sin(elapsed * ray.speed + ray.phase) * 0.12;
        const currentAngle = Math.PI / 2 + ray.baseAngle + sway;

        // Angle bounds for drawing beam cone
        const halfWidth = ray.width;
        const startAngle = currentAngle - halfWidth;
        const endAngle = currentAngle + halfWidth;

        const pulse = pulsating
          ? 0.7 + 0.3 * Math.sin(elapsed * 2 + ray.phase)
          : 1;

        const beamGradient = ctx.createRadialGradient(
          originX,
          originY,
          0,
          originX,
          originY,
          maxRadius * ray.lengthMult * fadeDistance
        );

        // Parse ray color into rgba
        const baseAlpha = ray.alpha * pulse * saturation;
        beamGradient.addColorStop(0, `rgba(180, 245, 225, ${Math.min(baseAlpha * 1.5, 0.45)})`);
        beamGradient.addColorStop(0.2, `rgba(54, 179, 126, ${Math.min(baseAlpha * 0.9, 0.3)})`);
        beamGradient.addColorStop(0.6, `rgba(24, 85, 74, ${Math.min(baseAlpha * 0.4, 0.15)})`);
        beamGradient.addColorStop(1, "rgba(4, 38, 33, 0)");

        ctx.fillStyle = beamGradient;
        ctx.beginPath();
        ctx.moveTo(originX, originY);
        ctx.arc(originX, originY, maxRadius, startAngle, endAngle);
        ctx.closePath();
        ctx.fill();
      });

      // Ambient center glow around origin
      const ambientGlow = ctx.createRadialGradient(
        originX,
        originY,
        0,
        originX,
        originY,
        width * 0.6
      );
      ambientGlow.addColorStop(0, "rgba(54, 179, 126, 0.22)");
      ambientGlow.addColorStop(0.5, "rgba(11, 95, 84, 0.08)");
      ambientGlow.addColorStop(1, "rgba(4, 38, 33, 0)");
      ctx.fillStyle = ambientGlow;
      ctx.beginPath();
      ctx.arc(originX, originY, width * 0.6, 0, Math.PI * 2);
      ctx.fill();

      ctx.restore();

      animationFrameId = requestAnimationFrame(render);
    };

    animationFrameId = requestAnimationFrame(render);

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener("resize", resize);
      window.removeEventListener("mousemove", onMouseMove);
    };
  }, [
    raysOrigin,
    raysColor,
    raysSpeed,
    lightSpread,
    rayLength,
    pulsating,
    fadeDistance,
    saturation,
    followMouse,
    mouseInfluence,
    noiseAmount,
    distortion,
  ]);

  return (
    <canvas
      ref={canvasRef}
      className="w-full h-full block"
      style={{ pointerEvents: "none" }}
    />
  );
}
