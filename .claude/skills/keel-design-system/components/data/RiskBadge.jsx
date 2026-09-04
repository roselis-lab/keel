import React from "react";

/**
 * Severity escalates by WEIGHT, not by hue: only critical is a solid fill, high is
 * a wash, medium moves to amber, low goes neutral. Low is not green — green means
 * "covered", a different axis. Nothing else on a report screen may be solid crimson.
 */
const SEV = {
  critical: { bg: "var(--sev-critical-bg)", fg: "var(--sev-critical-fg)", line: "var(--sev-critical-line)", weight: "var(--fw-bold)" },
  high:     { bg: "var(--sev-high-bg)", fg: "var(--sev-high-fg)", line: "var(--sev-high-line)", weight: "var(--fw-bold)" },
  medium:   { bg: "var(--sev-medium-bg)", fg: "var(--sev-medium-fg)", line: "var(--sev-medium-line)", weight: "var(--fw-semibold)" },
  low:      { bg: "var(--sev-low-bg)", fg: "var(--sev-low-fg)", line: "var(--sev-low-line)", weight: "var(--fw-medium)" },
  info:     { bg: "var(--sev-info-bg)", fg: "var(--sev-info-fg)", line: "transparent", weight: "var(--fw-medium)" },
};

/**
 * The spine colour for a ranked finding card's left edge. Read it straight from the
 * tokens — `var(--sev-<level>-spine)` — so no JS map has to stay in sync:
 *   style={{ borderLeft: "4px solid var(--sev-" + f.severity + "-spine)" }}
 * Or wrap the card in <SeveritySpine level={f.severity}>.
 */
export function SeveritySpine({ level = "info", width = 4, children, style }) {
  return (
    <div style={{ borderLeft: width + "px solid var(--sev-" + level + "-spine)", ...style }}>
      {children}
    </div>
  );
}

export function RiskBadge({ level = "info", prefix, style }) {
  const s = SEV[level] || SEV.info;
  return (
    <span
      style={{
        display: "inline-flex", alignItems: "center", gap: "5px",
        fontSize: "var(--fs-10)", padding: "1px 8px", borderRadius: "var(--r-4)",
        fontWeight: s.weight, whiteSpace: "nowrap", textTransform: "lowercase",
        background: s.bg, color: s.fg, border: "1px solid " + s.line,
        fontFamily: "var(--font-sans)", ...style,
      }}
    >
      {prefix ? <span style={{ opacity: 0.7, fontWeight: "var(--fw-medium)" }}>{prefix}</span> : null}
      {level}
    </span>
  );
}
