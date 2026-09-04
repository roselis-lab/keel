import React, { useState } from "react";

function Item({ value, label, checked, onToggle }) {
  const [hover, setHover] = useState(false);
  return (
    <label
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        display: "inline-flex", alignItems: "center", gap: "6px", padding: "6px 11px",
        border: "1px solid " + (hover ? "var(--crimson-200)" : "var(--navy-200)"),
        borderRadius: "var(--r-8)", fontSize: "var(--fs-13)", cursor: "pointer",
        background: "#fff", color: "var(--navy-800)",
      }}
    >
      <input
        type="checkbox"
        checked={checked}
        onChange={() => onToggle(value)}
        style={{ accentColor: "var(--crimson-600)", margin: 0 }}
      />
      {label}
    </label>
  );
}

/** Multi-value enum fields (surface, source) as a wrapping row of checkbox capsules. */
export function CheckSet({ options = [], value = [], onToggle = () => {}, style }) {
  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", ...style }}>
      {options.map(o => {
        const v = Array.isArray(o) ? o[0] : o;
        const l = Array.isArray(o) ? o[1] : o;
        return <Item key={v} value={v} label={l} checked={value.includes(v)} onToggle={onToggle} />;
      })}
    </div>
  );
}
