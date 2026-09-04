import React from "react";

/** The rail's top screen switcher. Inert tint strip; the active tab is white with a crimson underline. */
export function ScreenTabs({ screens = [], value, onChange, style }) {
  return (
    <nav style={{ display: "flex", ...style }}>
      {screens.map(s => {
        const v = Array.isArray(s) ? s[0] : s;
        const l = Array.isArray(s) ? s[1] : s;
        const on = v === value;
        return (
          <button key={v} type="button" onClick={() => onChange && onChange(v)}
            style={{
              flex: 1, border: "none", cursor: "pointer",
              background: on ? "var(--panel)" : "var(--tint)",
              color: on ? "var(--navy-900)" : "var(--navy-500)",
              fontFamily: "var(--font-sans)", fontSize: "var(--fs-12)",
              fontWeight: "var(--fw-semibold)", padding: "10px 8px",
              borderBottom: "2px solid " + (on ? "var(--crimson-600)" : "var(--border)"),
            }}>{l}</button>
        );
      })}
    </nav>
  );
}
