import React from "react";

/** A dashboard count. 28px/700, tabular, tight tracking. */
export function StatTile({ value, label, style }) {
  return (
    <div style={{
      flex: 1, minWidth: "120px", border: "1px solid var(--border)",
      borderRadius: "var(--r-10)", padding: "14px 16px", background: "#fff", ...style,
    }}>
      <div style={{
        fontSize: "var(--fs-28)", fontWeight: "var(--fw-bold)", color: "var(--navy-900)",
        letterSpacing: "var(--ls-number)", fontVariantNumeric: "var(--numeric)", lineHeight: 1.1,
      }}>{value}</div>
      <div style={{ fontSize: "var(--fs-12)", color: "var(--navy-500)", marginTop: "3px" }}>{label}</div>
    </div>
  );
}
