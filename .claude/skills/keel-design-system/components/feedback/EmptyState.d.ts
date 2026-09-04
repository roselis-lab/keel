import * as React from "react";

/** One line of muted text — never an illustration, never a call-to-action button. */
export interface EmptyStateProps {
  /** One short imperative sentence with a period: "Select a threat from the list." */
  children?: React.ReactNode;
  /** Top offset. 22vh in the editor pane, 40px in a rail, 10vh in the preview. */
  top?: string;
  style?: React.CSSProperties;
}
export declare function EmptyState(props: EmptyStateProps): JSX.Element;
