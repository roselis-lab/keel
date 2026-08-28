import * as React from "react";

/** The validation summary from POST /threats/validate. Errors block; advice never does. */
export interface ErrorSummaryProps {
  /** error = crimson (blocking). advice = amber (non-blocking). */
  tone?: "error" | "advice";
  /** e.g. "3 problems block this save" / "2 things worth a look". */
  title?: string;
  /** One line each, naming the field and the rule. Never apologise. */
  items?: React.ReactNode[];
  style?: React.CSSProperties;
}
export declare function ErrorSummary(props: ErrorSummaryProps): JSX.Element;
