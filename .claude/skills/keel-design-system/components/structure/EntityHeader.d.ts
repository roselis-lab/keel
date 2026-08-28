import * as React from "react";

/** The detail header above every read view and edit form. */
export interface EntityHeaderProps {
  /** One character in a 42px crimson tile — type, not artwork. "T" for a threat, "C" for a control. */
  glyph?: string;
  title: string;
  /** Mono id line, e.g. "T-TOOL-ABUSE". */
  id?: string;
  badges?: React.ReactNode;
  /** Edit / Save / Delete buttons. */
  actions?: React.ReactNode;
  style?: React.CSSProperties;
}
export declare function EntityHeader(props: EntityHeaderProps): JSX.Element;
