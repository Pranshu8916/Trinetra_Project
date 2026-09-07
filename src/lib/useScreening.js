"use client";

/**
 * useScreening.js
 * ───────────────
 * Custom React hook for the single-shot AI document screening workflow.
 *
 * Usage:
 *   const { status, result, error, screen, reset } = useScreening();
 *
 *   // Trigger a screen
 *   await screen(passportBlob, selfieBlob);
 *
 *   // Read the decision
 *   const { label, color, icon, action } = resolveDecision(result.risk_score);
 *
 * Status lifecycle:
 *   "idle" → "loading" → "success" | "error"
 */

import { useState, useCallback } from "react";
import { apiScreenDocument } from "@/lib/api";

// ─── Decision Resolver ────────────────────────────────────────────────────────
// Maps the numeric risk_score → UI decision object using exact contract thresholds.
// Pure function — no hook dependency, importable anywhere.

/**
 * @typedef {Object} DecisionUI
 * @property {string} label   - "Clean" | "Suspicious" | "Fraud/Impostor"
 * @property {string} color   - Tailwind/CSS semantic colour name
 * @property {string} hex     - Direct hex colour for non-Tailwind contexts
 * @property {string} icon    - Emoji / unicode icon
 * @property {string} action  - Human-readable gate action for operators
 * @property {"success"|"warning"|"danger"} severity - Semantic severity token
 */

/**
 * Resolve a risk score to a UI decision descriptor.
 *
 * Thresholds:
 *   < 40  → "Clean"          (Green Light  — Unlock e-Gate)
 *   40-74 → "Suspicious"     (Amber Alert  — Manual Inspection)
 *   >= 75 → "Fraud/Impostor" (Red Alarm    — Gate Lock & Detain)
 *
 * @param {number} riskScore - Risk score 0–100
 * @returns {DecisionUI}
 */
export function resolveDecision(riskScore) {
  if (typeof riskScore !== "number") {
    return {
      label:    "Unknown",
      color:    "gray",
      hex:      "#6b7280",
      icon:     "❓",
      action:   "Unable to determine decision — check backend response.",
      severity: "warning",
    };
  }

  if (riskScore < 40) {
    return {
      label:    "Clean",
      color:    "emerald",
      hex:      "#10b981",
      icon:     "🟢",
      action:   "e-Gate unlocked — standard entry authorised.",
      severity: "success",
    };
  }

  if (riskScore < 75) {
    return {
      label:    "Suspicious",
      color:    "amber",
      hex:      "#f59e0b",
      icon:     "🟡",
      action:   "Manual inspection required — refer to senior officer immediately.",
      severity: "warning",
    };
  }

  return {
    label:    "Fraud/Impostor",
    color:    "red",
    hex:      "#ef4444",
    icon:     "🔴",
    action:   "Gate locked — detain subject and escalate to security.",
    severity: "danger",
  };
}


// ─── Hook ─────────────────────────────────────────────────────────────────────

/**
 * @typedef {Object} ScreeningState
 * @property {"idle"|"loading"|"success"|"error"} status
 * @property {Object|null} result   - Full API response on success
 * @property {string|null} error    - Human-readable error message on failure
 * @property {DecisionUI|null} decision - Resolved decision UI descriptor
 * @property {Function} screen      - (passportBlob, liveFrameBlob, [opts]) => Promise<void>
 * @property {Function} reset       - Resets state back to idle
 */

/**
 * Custom hook for the single-shot AI document screening workflow.
 *
 * @returns {ScreeningState}
 */
export function useScreening() {
  const [status,   setStatus]   = useState("idle");
  const [result,   setResult]   = useState(null);
  const [error,    setError]    = useState(null);
  const [decision, setDecision] = useState(null);

  /**
   * Execute the single-shot screening pipeline.
   *
   * @param {Blob}   passportBlob    - Identity document image blob
   * @param {Blob}   liveFrameBlob   - Live webcam selfie blob
   * @param {Object} [opts]
   * @param {string} [opts.passportFilename="passport.png"]
   * @param {string} [opts.liveFilename="selfie.jpg"]
   */
  const screen = useCallback(async (
    passportBlob,
    liveFrameBlob,
    { passportFilename = "passport.png", liveFilename = "selfie.jpg" } = {},
  ) => {
    if (!passportBlob || !liveFrameBlob) {
      setError("Both a passport image and a live selfie are required.");
      setStatus("error");
      return;
    }

    setStatus("loading");
    setResult(null);
    setError(null);
    setDecision(null);

    try {
      const data = await apiScreenDocument(
        passportBlob,
        liveFrameBlob,
        passportFilename,
        liveFilename,
      );

      setResult(data);
      setDecision(resolveDecision(data.risk_score));
      setStatus("success");
    } catch (err) {
      setError(err.message || "Screening failed. Please check the backend connection.");
      setStatus("error");
    }
  }, []);

  /** Reset hook state back to idle. */
  const reset = useCallback(() => {
    setStatus("idle");
    setResult(null);
    setError(null);
    setDecision(null);
  }, []);

  return { status, result, error, decision, screen, reset };
}
