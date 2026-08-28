import React from "react";

/** The bottom-right confirmation. Past tense, terse, gone in 2.2s. */
export function Toast({ message, tone = "neutral", show = true, style }) {
  return (
    <div style={{
      position: "fixed", bottom: "20px", right: "22px",
      background: tone === "error" ? "var(--crimson-700)" : "var(--navy-900)",
      color: "#fff", padding: "10px 16px", borderRadius: "var(--r-10)",
      fontFamily: "var(--font-sans)", fontSize: "var(--fs-13)",
      boxShadow: "var(--shadow-toast)",
      opacity: show ? 1 : 0,
      transform: show ? "translateY(0)" : "translateY(var(--toast-rise))",
      transition: "opacity var(--dur-layer), transform var(--dur-layer)",
      pointerEvents: "none", zIndex: 50, ...style,
    }}>{message}</div>
  );
}
