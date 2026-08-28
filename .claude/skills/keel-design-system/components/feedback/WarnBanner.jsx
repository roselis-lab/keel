import React from "react";

/** An inline caveat on a read view — a dangling link, an un-gated threat. */
export function WarnBanner({ tone = "error", children, style }) {
  const ok = tone === "ok";
  return (
    <div style={{
      background: ok ? "var(--green-50)" : "var(--crimson-50)",
      border: "1px solid " + (ok ? "var(--green-200)" : "var(--crimson-200)"),
      color: ok ? "var(--green)" : "var(--crimson-700)",
      borderRadius: "var(--r-8)", padding: "9px 12px",
      fontFamily: "var(--font-sans)", fontSize: "var(--fs-13)", lineHeight: 1.5, ...style,
    }}>{children}</div>
  );
}
