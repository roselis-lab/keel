import React from "react";
import { Chip } from "../core/Chip.jsx";

/** The collapsed "Filters (N)" expander in the rail. OR within a group, AND across groups. */
export function FacetPanel({ groups = [], selected = {}, open, activeCount = 0, onOpen, onToggle, onClear, style }) {
  return (
    <div style={{ borderBottom: "1px solid var(--border)", ...style }}>
      <div
        onClick={() => onOpen && onOpen(!open)}
        style={{
          display: "flex", alignItems: "center", gap: "7px", padding: "8px 14px",
          cursor: "pointer", userSelect: "none",
        }}
      >
        <span aria-hidden="true" style={{ color: "var(--navy-400)", fontSize: "var(--fs-10)", width: "10px", flexShrink: 0 }}>{open ? "▾" : "▸"}</span>
        <span style={{ fontSize: "var(--fs-12)", fontWeight: "var(--fw-semibold)", color: "var(--navy-700)" }}>Filters</span>
        {activeCount ? <span style={{
          fontSize: "var(--fs-10)", fontWeight: "var(--fw-bold)", padding: "1px 7px",
          borderRadius: "var(--r-pill)", background: "var(--crimson-600)", color: "#fff",
          fontVariantNumeric: "var(--numeric)",
        }}>{activeCount}</span> : null}
        {activeCount ? (
          <button type="button" onClick={e => { e.stopPropagation(); onClear && onClear(); }} style={{
            marginLeft: "auto", border: "none", background: "none", color: "var(--navy-500)",
            fontSize: "var(--fs-11)", fontWeight: "var(--fw-semibold)", padding: "2px 4px",
            borderRadius: "var(--r-6)", cursor: "pointer",
          }}>Clear all</button>
        ) : null}
      </div>
      {open ? (
        <div style={{ padding: "2px 14px 10px", maxHeight: "46vh", overflowY: "auto" }}>
          {groups.map((g, gi) => (
            <div key={g.key} style={{ marginTop: gi === 0 ? "4px" : "9px" }}>
              <p style={{
                fontSize: "var(--fs-10)", textTransform: "uppercase", letterSpacing: "var(--ls-key)",
                color: "var(--navy-500)", fontWeight: "var(--fw-bold)", margin: "0 0 5px",
              }}>{g.label}</p>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "5px" }}>
                {g.options.map(o => {
                  const v = Array.isArray(o) ? o[0] : o;
                  const l = Array.isArray(o) ? o[1] : o;
                  return (
                    <Chip key={v} selected={(selected[g.key] || []).includes(v)}
                      onClick={() => onToggle && onToggle(g.key, v)}>{l}</Chip>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}
