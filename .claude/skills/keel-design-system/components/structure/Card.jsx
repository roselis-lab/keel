import React, { useState } from "react";

/** A white card on a tint band — a weakness, a mitigation link, a report finding. */
export function Card({ id, title, rationale, desc, badges, jump, onClick, children, style }) {
  const [hover, setHover] = useState(false);
  const interactive = Boolean(jump || onClick);
  return (
    <div
      onClick={onClick}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        border: "1px solid " + (interactive && hover ? "var(--crimson-200)" : "var(--border)"),
        background: interactive && hover ? "var(--crimson-50)" : "#fff",
        borderRadius: "var(--r-10)", padding: "var(--pad-card)", marginBottom: "10px",
        cursor: interactive ? "pointer" : "default",
        transition: "background var(--dur-hover), border-color var(--dur-hover)",
        ...style,
      }}
    >
      {(id || title || badges) ? (
        <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
          {id ? <span style={{ fontFamily: "var(--font-mono)", fontSize: "var(--fs-11)", color: "var(--navy-400)" }}>{id}</span> : null}
          {title ? <span style={{ fontWeight: "var(--fw-semibold)", color: "var(--navy-900)", fontSize: "var(--fs-14)" }}>{title}</span> : null}
          {badges}
        </div>
      ) : null}
      {desc ? <p style={{ margin: "6px 0 0", color: "var(--navy-600)", fontSize: "var(--fs-13)", whiteSpace: "pre-wrap", lineHeight: 1.5 }}>{desc}</p> : null}
      {rationale ? <p style={{ margin: "7px 0 0", color: "var(--navy-500)", fontSize: "var(--fs-13)", fontStyle: "italic", whiteSpace: "pre-wrap", lineHeight: 1.5 }}>{rationale}</p> : null}
      {children}
    </div>
  );
}
