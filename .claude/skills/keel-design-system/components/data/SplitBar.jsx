import React from "react";

const FILL = {
  verified: "var(--green)", shared: "var(--green)", ok: "var(--green)",
  draft: "var(--amber)", local: "var(--amber)",
  unset: "var(--navy-200)", none: "var(--navy-200)",
};

/** A 10px proportional bar plus its dot legend — draft vs verified, linked vs orphaned. */
export function SplitBar({ segments = [], style }) {
  const total = segments.reduce((n, s) => n + s.value, 0) || 1;
  return (
    <div style={style}>
      <div style={{
        display: "flex", height: "10px", borderRadius: "var(--r-6)",
        overflow: "hidden", background: "var(--navy-100)", margin: "8px 0 6px",
      }}>
        {segments.map((s, i) => (
          <div key={i} style={{ height: "100%", width: (s.value / total * 100) + "%", background: FILL[s.tone] || FILL.unset }} />
        ))}
      </div>
      <div style={{ display: "flex", gap: "14px", fontSize: "var(--fs-12)", color: "var(--navy-500)", flexWrap: "wrap" }}>
        {segments.map((s, i) => (
          <span key={i}>
            <span aria-hidden="true" style={{
              display: "inline-block", width: "8px", height: "8px", borderRadius: "var(--r-round)",
              marginRight: "4px", verticalAlign: "middle", background: FILL[s.tone] || FILL.unset,
            }} />
            {s.label}
            <span style={{ fontVariantNumeric: "var(--numeric)" }}> {s.value}</span>
          </span>
        ))}
      </div>
    </div>
  );
}
