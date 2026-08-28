import React, { useState } from "react";

/** The single-line text control. 38px min-height, crimson focus ring. */
export function TextInput({ invalid, mono, title, style, ...rest }) {
  const [focus, setFocus] = useState(false);
  return (
    <input
      type="text"
      onFocus={() => setFocus(true)}
      onBlur={() => setFocus(false)}
      style={{
        width: "100%", minHeight: "var(--input-h)", border: "1px solid var(--navy-200)",
        borderRadius: "var(--r-8)", padding: "8px 10px",
        fontFamily: mono ? "var(--font-mono)" : "var(--font-sans)",
        fontSize: title ? "var(--fs-19)" : "var(--fs-14)",
        fontWeight: title ? "var(--fw-bold)" : "var(--fw-regular)",
        lineHeight: "var(--lh-base)", color: "var(--navy-900)", background: "#fff", outline: "none",
        borderColor: focus ? "var(--crimson-600)" : invalid ? "var(--crimson-200)" : "var(--navy-200)",
        boxShadow: focus ? "var(--focus-ring)" : "none",
        ...style,
      }}
      {...rest}
    />
  );
}
