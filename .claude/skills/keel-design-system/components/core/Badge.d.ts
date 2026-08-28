import * as React from "react";

/** A word in a coloured pill — harm class, mitigation class, status, coverage. */
export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  /**
   * soft = neutral pill (navy-100, pill radius). type = navy-200 hard corner.
   * harm = solid crimson. danger/ok/advice = the three status washes. orphan = navy-200.
   */
  tone?: "soft" | "type" | "harm" | "danger" | "ok" | "advice" | "orphan";
  /** Turn on tabular-nums — use for coverage percentages and counts. */
  numeric?: boolean;
  /** Render the label in the mono stack — use for enum values and ids. */
  mono?: boolean;
  children?: React.ReactNode;
}
export declare function Badge(props: BadgeProps): JSX.Element;
