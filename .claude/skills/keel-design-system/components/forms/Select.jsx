import React, { useState } from "react";

/** A fixed-vocabulary dropdown. Options always come from the JSON Schema, never hardcoded. */
export function Select({ invalid, options = [], placeholder, style, ...rest }) {
  const [focus, setFocus] = useState(false);
  return (
    <select
      onFocus={() => setFocus(true)}
      onBlur={() => setFocus(false)}
      style={{
        width: "100%", minHeight: "var(--input-h)", border: "1px solid var(--navy-200)",
        borderRadius: "var(--r-8)", padding: "8px 10px", fontFamily: "var(--font-sans)",
        fontSize: "var(--fs-14)", lineHeight: "var(--lh-base)", color: "var(--navy-900)",
        background: "#fff", outline: "none",
        borderColor: focus ? "var(--crimson-600)" : invalid ? "var(--crimson-200)" : "var(--navy-200)",
        boxShadow: focus ? "var(--focus-ring)" : "none",
        ...style,
      }}
      {...rest}
    >
      {placeholder ? <option value="">{placeholder}</option> : null}
      {options.map(o => {
        const value = Array.isArray(o) ? o[0] : o;
        const label = Array.isArray(o) ? o[1] : o;
        return <option key={value} value={value}>{label}</option>;
      })}
    </select>
  );
}
