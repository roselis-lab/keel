import React, { useState } from "react";

/** A list row in the left rail. Selected = crimson wash + a 3px inset crimson accent. */
export function RailRow({ id, title, badges, selected, onClick, style }) {
  const [hover, setHover] = useState(false);
  return (
    <div
      onClick={onClick}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        padding: "var(--pad-rail-row)", borderBottom: "1px solid var(--border2)",
        display: "flex", flexDirection: "column", gap: "2px", cursor: "pointer",
        background: selected ? "var(--crimson-50)" : hover ? "var(--navy-100)" : "transparent",
        boxShadow: selected ? "var(--selected-rail-accent)" : "none",
        ...style,
      }}
    >
      {id ? <span style={{
        fontSize: "var(--fs-11)", color: "var(--navy-500)",
        fontFamily: "var(--font-mono)", letterSpacing: ".01em",
      }}>{id}</span> : null}
      <span style={{
        fontSize: "var(--fs-14)", color: "var(--navy-900)",
        fontWeight: "var(--fw-medium)", lineHeight: "var(--lh-tight)",
      }}>{title}</span>
      {badges ? <div style={{ display: "flex", gap: "5px", flexWrap: "wrap", marginTop: "3px" }}>{badges}</div> : null}
    </div>
  );
}
