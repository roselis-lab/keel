import React, { useState } from "react";

/** A bare Unicode glyph in a small hit area — rail collapse, card remove, disclosure. */
export function IconButton({ glyph, tone = "neutral", title, style, ...rest }) {
  const [hover, setHover] = useState(false);
  const danger = tone === "danger";
  return (
    <button
      type="button"
      title={title}
      aria-label={title}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        border: "none", background: hover ? (danger ? "var(--crimson-50)" : "var(--navy-100)") : "none",
        color: hover ? (danger ? "var(--crimson-600)" : "var(--navy-800)") : "var(--navy-400)",
        fontFamily: "var(--font-sans)", fontSize: "15px", lineHeight: 1,
        padding: "3px 6px", borderRadius: "var(--r-6)", flexShrink: 0, cursor: "pointer",
        ...style,
      }}
      {...rest}
    >
      {glyph}
    </button>
  );
}
