import React from "react";

/** Two channels, never one: red blocks the save, amber advises and never blocks. */
export function ErrorSummary({ tone = "error", title, items = [], style }) {
  const err = tone === "error";
  return (
    <div style={{
      background: err ? "var(--crimson-50)" : "var(--amber-50)",
      border: "1px solid " + (err ? "var(--crimson-200)" : "var(--amber)"),
      color: err ? "var(--crimson-700)" : "var(--amber)",
      borderRadius: "var(--r-8)", padding: "10px 14px", margin: "16px 0 4px",
      fontFamily: "var(--font-sans)", fontSize: "var(--fs-13)", lineHeight: 1.5, ...style,
    }}>
      {title ? <strong style={{ display: "block", marginBottom: "5px" }}>{title}</strong> : null}
      <ul style={{ margin: 0, paddingLeft: "18px" }}>
        {items.map((it, i) => <li key={i}>{it}</li>)}
      </ul>
    </div>
  );
}
