import React, { useState } from "react";

function Crumb({ children, onClick }) {
  const [h, setH] = useState(false);
  return (
    <button type="button" onClick={onClick}
      onMouseEnter={() => setH(true)} onMouseLeave={() => setH(false)}
      style={{
        border: "none", background: "none", padding: 0, font: "inherit",
        fontWeight: "var(--fw-semibold)", cursor: "pointer",
        color: h ? "var(--crimson-600)" : "var(--navy-500)",
        textDecoration: h ? "underline" : "none",
      }}>{children}</button>
  );
}

/** The quiet type/id line above a read view, plus its optional provenance line. */
export function Breadcrumb({ type, id, onType, lastChanged, onViewChange, style }) {
  return (
    <div style={style}>
      <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "var(--fs-12)", color: "var(--navy-400)", marginBottom: "12px" }}>
        <Crumb onClick={onType}>{type}</Crumb>
        <span style={{ color: "var(--navy-400)" }}>/</span>
        <span style={{ fontFamily: "var(--font-mono)", color: "var(--navy-500)" }}>{id}</span>
      </div>
      {lastChanged ? (
        <p style={{ fontSize: "var(--fs-12)", color: "var(--navy-400)", margin: "-4px 0 12px" }}>
          {lastChanged}
          {onViewChange ? (
            <button type="button" onClick={onViewChange} style={{
              border: "none", background: "none", color: "var(--crimson-600)",
              fontWeight: "var(--fw-semibold)", fontSize: "var(--fs-12)", padding: "0 0 0 4px", cursor: "pointer",
            }}>view change</button>
          ) : null}
        </p>
      ) : null}
    </div>
  );
}
