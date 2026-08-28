import React from "react";

/** A per-entity coverage row: mono field name, then a graded badge. */
export function CoverageBar({ label, percent, orphan, style }) {
  const grade = percent >= 80 ? "ok" : percent >= 40 ? "advice" : "danger";
  const skin = orphan
    ? { bg: "var(--navy-200)", fg: "var(--navy-600)" }
    : grade === "ok" ? { bg: "var(--green-50)", fg: "var(--green)" }
    : grade === "advice" ? { bg: "var(--amber-50)", fg: "var(--amber)" }
    : { bg: "var(--crimson-50)", fg: "var(--crimson-700)" };
  return (
    <div style={{
      display: "flex", alignItems: "center", justifyContent: "space-between", gap: "8px",
      padding: "7px 0", borderBottom: "1px solid var(--border2)", ...style,
    }}>
      <span style={{ fontSize: "var(--fs-13)", color: "var(--navy-700)", fontFamily: "var(--font-mono)" }}>{label}</span>
      <span style={{
        fontSize: "var(--fs-10)", padding: "1px 8px", borderRadius: "var(--r-4)",
        fontWeight: "var(--fw-semibold)", whiteSpace: "nowrap",
        background: skin.bg, color: skin.fg, fontVariantNumeric: "var(--numeric)",
      }}>{orphan ? "orphan" : percent + "%"}</span>
    </div>
  );
}
