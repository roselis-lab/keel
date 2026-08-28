import React, { useState } from "react";

/** The multi-line prose control — weakness text, reachability, rationale. */
export function TextArea({ invalid, rows = 4, style, ...rest }) {
  const [focus, setFocus] = useState(false);
  return (
    <textarea
      rows={rows}
      onFocus={() => setFocus(true)}
      onBlur={() => setFocus(false)}
      style={{
        width: "100%", border: "1px solid var(--navy-200)", borderRadius: "var(--r-8)",
        padding: "8px 10px", fontFamily: "var(--font-sans)", fontSize: "var(--fs-14)",
        lineHeight: "var(--lh-base)", color: "var(--navy-900)", background: "#fff",
        outline: "none", resize: "vertical",
        borderColor: focus ? "var(--crimson-600)" : invalid ? "var(--crimson-200)" : "var(--navy-200)",
        boxShadow: focus ? "var(--focus-ring)" : "none",
        ...style,
      }}
      {...rest}
    />
  );
}
