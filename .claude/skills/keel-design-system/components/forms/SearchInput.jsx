import React, { useState } from "react";

/** The rail filter field: tint fill that goes white on focus, 9px radius. */
export function SearchInput({ style, ...rest }) {
  const [focus, setFocus] = useState(false);
  return (
    <div style={{ padding: "10px 14px", borderBottom: "1px solid var(--border)", ...style }}>
      <input
        type="search"
        autoComplete="off"
        onFocus={() => setFocus(true)}
        onBlur={() => setFocus(false)}
        style={{
          width: "100%", padding: "9px 11px",
          background: focus ? "#fff" : "var(--tint)", color: "var(--navy-900)",
          border: "1px solid " + (focus ? "var(--crimson-600)" : "var(--border)"),
          borderRadius: "var(--r-9)", outline: "none",
          fontFamily: "var(--font-sans)", fontSize: "var(--fs-13)",
        }}
        {...rest}
      />
    </div>
  );
}
