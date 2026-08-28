import * as React from "react";

/**
 * The form's atom: uppercase label, one reserved-height hint line, the control, then
 * at most one validation message. Errors block a save; advice never does.
 */
export interface FieldProps {
  /** Authored in sentence case — CSS uppercases it. */
  label?: string;
  /** Exactly one short line, truncated. Longer guidance goes in `guidance`. */
  hint?: string;
  /** Red, blocking. Renders a crimson dot on the label. */
  error?: string;
  /** Amber, non-blocking. Suppressed when `error` is set. */
  advice?: string;
  /** Collapsed "How to write this" panel — the style guide's slots for this field. */
  guidance?: React.ReactNode;
  /** Keep the 17px hint row even with no hint, so adjacent fields align. Default true. */
  reserveHint?: boolean;
  children?: React.ReactNode;
  style?: React.CSSProperties;
}
export declare function Field(props: FieldProps): JSX.Element;
