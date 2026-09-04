import React from "react";
import { IconButton } from "../core/IconButton.jsx";

/** A collapsible repeatable form record. Its border is the only heavy container in a form. */
export function EditorCard({ summary, open = true, hasError, onToggle, onRemove, children, style }) {
  return (
    <div style={{
      position: "relative", border: "1px solid " + (hasError && !open ? "var(--crimson-200)" : "var(--border)"),
      borderRadius: "var(--r-10)", marginBottom: "10px", background: "var(--tint)", ...style,
    }}>
      <div
        onClick={onToggle}
        style={{
          display: "flex", alignItems: "center", gap: "8px",
          padding: open ? "10px 12px" : "9px 12px", cursor: "pointer", userSelect: "none",
        }}
      >
        <IconButton glyph={open ? "▾" : "▸"} title={open ? "Collapse" : "Expand"} style={{ fontSize: "11px", padding: "2px 3px" }} />
        <span style={{
          flex: 1, minWidth: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
          fontSize: "var(--fs-13)", color: "var(--navy-700)", fontWeight: "var(--fw-semibold)",
          fontFamily: "var(--font-mono)",
        }}>{summary}</span>
        {hasError && !open ? <span aria-hidden="true" style={{
          display: "inline-block", width: "8px", height: "8px", borderRadius: "var(--r-round)",
          background: "var(--crimson-600)", flexShrink: 0,
        }} /> : null}
        {onRemove ? <IconButton glyph="×" tone="danger" title="Remove" onClick={e => { e.stopPropagation(); onRemove(); }} /> : null}
      </div>
      {open ? <div style={{ padding: "2px 14px 14px" }}>{children}</div> : null}
    </div>
  );
}
