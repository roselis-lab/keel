import React, { useState } from "react";

/** A multi-select filter chip, or a clickable jump chip. Selected = solid crimson. */
export function Chip({ selected, variant = "facet", mono, children, style, ...rest }) {
  const [hover, setHover] = useState(false);
  const jump = variant === "jump";
  const base = {
    fontFamily: mono || jump ? "var(--font-mono)" : "var(--font-sans)",
    fontSize: jump ? "var(--fs-12)" : "var(--fs-11)",
    padding: jump ? "3px 9px" : "2px 9px",
    borderRadius: jump ? "var(--r-6)" : "var(--r-pill)",
    fontWeight: "var(--fw-medium)", whiteSpace: "nowrap", cursor: "pointer",
    border: "1px solid var(--border)", display: "inline-flex", alignItems: "center",
  };
  let skin;
  if (selected) {
    skin = { background: hover ? "var(--crimson-700)" : "var(--crimson-600)", color: "#fff", borderColor: "var(--crimson-600)" };
  } else if (hover) {
    skin = jump
      ? { background: "var(--crimson-50)", color: "var(--crimson-700)", borderColor: "var(--crimson-200)" }
      : { background: "var(--tint)", color: "var(--crimson-700)", borderColor: "var(--crimson-200)" };
  } else {
    skin = jump
      ? { background: "var(--navy-100)", color: "var(--navy-700)" }
      : { background: "var(--tint)", color: "var(--navy-600)" };
  }
  return (
    <button
      type="button"
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{ ...base, ...skin, ...style }}
      {...rest}
    >
      {children}
    </button>
  );
}
