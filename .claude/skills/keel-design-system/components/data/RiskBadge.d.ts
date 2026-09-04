import * as React from "react";

/**
 * A report finding's severity or likelihood grade.
 *
 * Severity is a WEIGHT ramp, so it outranks every other use of crimson on the page:
 * critical is the only solid crimson fill anywhere on a report screen, high is a
 * crimson wash, medium moves to amber, low is neutral navy. Low is deliberately not
 * green — green means "covered/closed", which is a different axis from severity.
 *
 * Because critical owns the solid fill, classification badges on the same screen
 * (harm, surface, source, mitigation class, complexity) must be neutral `type` badges.
 */
export interface RiskBadgeProps {
  level?: "critical" | "high" | "medium" | "low" | "info";
  /** A qualifier before the level, e.g. "severity" or "likelihood". Rendered at 70% opacity. */
  prefix?: string;
  style?: React.CSSProperties;
}
export declare function RiskBadge(props: RiskBadgeProps): JSX.Element;

/**
 * The 4px severity spine on a ranked finding card's left edge. The colour lives in
 * the tokens as `--sev-<level>-spine`, so you can equally write the border yourself:
 * `borderLeft: "4px solid var(--sev-" + level + "-spine)"`.
 */
export interface SeveritySpineProps {
  level?: "critical" | "high" | "medium" | "low" | "info";
  /** Border width in px. Default 4. */
  width?: number;
  children?: React.ReactNode;
  style?: React.CSSProperties;
}
export declare function SeveritySpine(props: SeveritySpineProps): JSX.Element;
