import * as React from "react";

/**
 * A unified diff rendered as two line-number gutters plus a pre content cell.
 * Uses GitHub's diff colours on purpose — it is quoting another tool's convention.
 * @startingPoint section="Data" subtitle="Unified git diff with line-number gutters" viewport="700x300"
 */
export interface DiffViewProps {
  /** The changed path, shown as a small mono caption. */
  file?: string;
  /** Raw unified-diff text. `@@` hunk headers drive the line counters. */
  patch?: string;
  loading?: boolean;
  style?: React.CSSProperties;
}
export declare function DiffView(props: DiffViewProps): JSX.Element;
