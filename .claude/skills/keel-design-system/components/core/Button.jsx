import React, { useState } from "react";

const SIZES = {
  md: { padding: "7px 13px", fontSize: "var(--fs-13)" },
  sm: { padding: "4px 9px", fontSize: "var(--fs-12)" },
};

const FILLS = {
  primary: { rest: "var(--crimson-600)", hover: "var(--crimson-700)", fg: "#fff" },
  ghost: { rest: "var(--navy-100)", hover: "var(--navy-200)", fg: "var(--navy-700)" },
  bare: { rest: "transparent", hover: "var(--navy-100)", fg: "var(--navy-700)" },
};

/** Keel's only button. Crimson fill = the one primary action on a screen. */
export function Button({ variant = "ghost", size = "md", disabled, glyph, children, style, ...rest }) {
  const [hover, setHover] = useState(false);
  const f = FILLS[variant] || FILLS.ghost;
  return (
    <button
      type="button"
      disabled={disabled}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        display: "inline-flex", alignItems: "center", gap: "6px", whiteSpace: "nowrap",
        border: "1px solid transparent", borderRadius: "var(--r-8)",
        fontFamily: "var(--font-sans)", fontWeight: "var(--fw-semibold)",
        lineHeight: 1.4, cursor: disabled ? "default" : "pointer",
        background: disabled || !hover ? f.rest : f.hover,
        color: f.fg, opacity: disabled ? 0.5 : 1,
        ...SIZES[size], ...style,
      }}
      {...rest}
    >
      {glyph ? <span aria-hidden="true">{glyph}</span> : null}
      {children}
    </button>
  );
}
