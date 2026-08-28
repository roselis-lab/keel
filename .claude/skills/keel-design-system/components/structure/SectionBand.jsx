import React from "react";

/**
 * The band that carries a section. Read view and edit form wear the SAME surface,
 * so toggling Edit never makes the eye lose its place — that is review-first in CSS.
 */
export function SectionBand({ label, sub, as = "section", count, children, style }) {
  const isForm = as === "fieldset";
  const Tag = isForm ? "fieldset" : "section";
  const LabelTag = isForm ? "legend" : "h3";
  return (
    <Tag style={{
      background: "var(--tint)", border: "1px solid var(--border2)",
      borderRadius: "var(--r-10)", padding: "var(--pad-section)",
      margin: isForm ? "14px 0 0" : 0, marginTop: "14px", minWidth: 0, ...style,
    }}>
      {label ? (
        <LabelTag style={{
          display: "block", width: "100%", float: "none", padding: 0, margin: "0 0 9px",
          fontSize: "var(--fs-11)", textTransform: "uppercase", letterSpacing: "var(--ls-eyebrow)",
          color: "var(--navy-700)", fontWeight: "var(--fw-bold)",
        }}>
          {label}
          {sub ? <span style={{ fontWeight: "var(--fw-regular)", textTransform: "none", color: "var(--navy-400)" }}> {sub}</span> : null}
          {count != null ? <span style={{
            color: "var(--navy-400)", fontSize: "var(--fs-11)", fontWeight: "var(--fw-medium)",
            textTransform: "none", letterSpacing: 0, marginLeft: "8px",
          }}>{count}</span> : null}
        </LabelTag>
      ) : null}
      {children}
    </Tag>
  );
}
