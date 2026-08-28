import * as React from "react";

/**
 * A section surface: tint fill, --border2 hairline, 10px radius, 12px 14px padding.
 * Use the identical band for a read section and for its edit fieldset.
 * @startingPoint section="Structure" subtitle="Read band and edit fieldset on one surface" viewport="700x260"
 */
export interface SectionBandProps {
  /** Sentence case; rendered uppercase at 11px/700 with .08em tracking. */
  label?: string;
  /** A muted non-uppercase suffix on the label line, e.g. "(judged un-mitigated)". */
  sub?: string;
  /** "section" for the read view, "fieldset" for the edit form (legend replaces h3). */
  as?: "section" | "fieldset";
  /** A muted count on the label line, e.g. "4 authored". */
  count?: string | number;
  children?: React.ReactNode;
  style?: React.CSSProperties;
}
export declare function SectionBand(props: SectionBandProps): JSX.Element;
