import React from "react";

const FILL = { error: "var(--crimson-600)", advice: "var(--amber)", ok: "var(--green)", none: "var(--navy-200)" };

/** The status marker: an 8px CSS circle. Keel draws status, never an icon for it. */
export function Dot({ tone = "none", size = 8, style, ...rest }) {
  return (
    <span
      aria-hidden="true"
      style={{
        display: "inline-block", width: size + "px", height: size + "px",
        borderRadius: "var(--r-round)", background: FILL[tone] || FILL.none,
        verticalAlign: "middle", flexShrink: 0, ...style,
      }}
      {...rest}
    />
  );
}
