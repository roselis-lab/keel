import React from "react";
import { Chip } from "../core/Chip.jsx";

/** Empty is information: unauthored fields come back as chips that jump into edit. */
export function GapChips({ label = "Gaps to review", items = [], onPick, dashed = true, style }) {
  return (
    <div style={{
      marginTop: "var(--section-gap)",
      borderTop: dashed ? "1px dashed var(--border)" : "none",
      paddingTop: "14px", ...style,
    }}>
      <span style={{
        display: "block", fontSize: "var(--fs-11)", textTransform: "uppercase",
        letterSpacing: ".07em", color: "var(--navy-500)", fontWeight: "var(--fw-bold)", margin: "0 0 9px",
      }}>{label}</span>
      <div style={{ display: "flex", flexWrap: "wrap", gap: "7px" }}>
        {items.map(it => {
          const v = Array.isArray(it) ? it[0] : it;
          const l = Array.isArray(it) ? it[1] : it;
          return <Chip key={v} variant="jump" onClick={() => onPick && onPick(v)}>{l}</Chip>;
        })}
      </div>
    </div>
  );
}
