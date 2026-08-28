import React from "react";

/** The detail-page header: letter tile, title, mono id, badges, actions. */
export function EntityHeader({ glyph, title, id, badges, actions, style }) {
  return (
    <div style={{
      display: "flex", alignItems: "flex-start", gap: "14px",
      paddingBottom: "20px", marginBottom: "4px", borderBottom: "1px solid var(--border)", ...style,
    }}>
      {glyph ? (
        <div style={{
          width: "42px", height: "42px", borderRadius: "var(--r-10)",
          display: "flex", alignItems: "center", justifyContent: "center",
          color: "#fff", flexShrink: 0, fontSize: "20px", fontWeight: "var(--fw-bold)",
          background: "var(--crimson-600)",
        }}>{glyph}</div>
      ) : null}
      <div style={{ flex: 1, minWidth: 0 }}>
        <h2 style={{ margin: 0, fontSize: "var(--fs-20)", fontWeight: "var(--fw-bold)", letterSpacing: "var(--ls-title)", color: "var(--navy-900)" }}>{title}</h2>
        {id ? <div style={{ fontFamily: "var(--font-mono)", color: "var(--navy-400)", fontSize: "var(--fs-12)", marginTop: "4px" }}>{id}</div> : null}
        {badges ? <div style={{ display: "flex", gap: "5px", flexWrap: "wrap", marginTop: "8px" }}>{badges}</div> : null}
      </div>
      {actions ? <div style={{ display: "flex", gap: "8px", flexShrink: 0 }}>{actions}</div> : null}
    </div>
  );
}
