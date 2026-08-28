import React from "react";

/** label + one-line hint + control + validation message. The whole form is these. */
export function Field({ label, hint, error, advice, guidance, reserveHint = true, children, style }) {
  const dot = error ? "var(--crimson-600)" : advice ? "var(--amber)" : null;
  return (
    <div style={{ position: "relative", minWidth: 0, ...style }}>
      {label ? (
        <div style={{
          fontSize: "var(--fs-11)", textTransform: "uppercase", letterSpacing: "var(--ls-eyebrow)",
          color: "var(--navy-700)", fontWeight: "var(--fw-bold)", margin: "0 0 9px",
          display: "flex", alignItems: "center",
        }}>
          {label}
          {dot ? <span aria-hidden="true" style={{
            display: "inline-block", width: "8px", height: "8px", borderRadius: "var(--r-round)",
            background: dot, marginLeft: "8px",
          }} /> : null}
        </div>
      ) : null}
      {hint || reserveHint ? (
        <p style={{
          color: "var(--navy-500)", fontSize: "var(--fs-12)", lineHeight: 1.4, margin: "0 0 6px",
          minHeight: "17px", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis",
        }}>{hint}</p>
      ) : null}
      {children}
      {error ? <p style={{ fontSize: "var(--fs-12)", marginTop: "5px", lineHeight: 1.4, color: "var(--crimson-700)" }}>{error}</p> : null}
      {!error && advice ? <p style={{ fontSize: "var(--fs-12)", marginTop: "5px", lineHeight: 1.4, color: "var(--amber)" }}>{advice}</p> : null}
      {guidance ? (
        <details style={{ marginTop: "8px" }}>
          <summary style={{
            listStyle: "none", cursor: "pointer", display: "inline-flex", alignItems: "center", gap: "5px",
            fontSize: "var(--fs-11)", fontWeight: "var(--fw-semibold)", color: "var(--navy-500)", padding: "2px 0",
          }}>
            <span aria-hidden="true" style={{ color: "var(--navy-400)", fontSize: "13px" }}>{"\u24D8"}</span>
            How to write this
          </summary>
          <div style={{
            marginTop: "6px", padding: "10px 12px", background: "#fff",
            border: "1px solid var(--navy-200)", borderRadius: "var(--r-8)",
            fontSize: "var(--fs-12)", color: "var(--navy-600)", lineHeight: 1.5,
          }}>{guidance}</div>
        </details>
      ) : null}
    </div>
  );
}
