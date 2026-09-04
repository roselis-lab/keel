import * as React from "react";

/** The only entrance animation in Keel: fade + 8px rise, 200ms, bottom-right. */
export interface ToastProps {
  /** Past tense and terse: "Saved.", "Nothing to save." */
  message: string;
  /** error = crimson-700 fill. neutral = navy-900. */
  tone?: "neutral" | "error";
  show?: boolean;
  style?: React.CSSProperties;
}
export declare function Toast(props: ToastProps): JSX.Element;
