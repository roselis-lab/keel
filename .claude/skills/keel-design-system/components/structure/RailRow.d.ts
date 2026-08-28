import * as React from "react";

/**
 * A left-rail list row: mono id above, title below.
 * @startingPoint section="Structure" subtitle="Rail rows with selection and badges" viewport="700x220"
 */
export interface RailRowProps {
  /** Mono secondary line, e.g. "T-DATA-LEAK". */
  id?: string;
  /** The primary line — 14px/500. */
  title: string;
  badges?: React.ReactNode;
  /** crimson-50 wash + inset 3px crimson-600 accent; suppresses hover. */
  selected?: boolean;
  onClick?: () => void;
  style?: React.CSSProperties;
}
export declare function RailRow(props: RailRowProps): JSX.Element;
