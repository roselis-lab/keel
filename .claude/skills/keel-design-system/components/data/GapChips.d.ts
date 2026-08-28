import * as React from "react";

/**
 * The foot of a read view: every unauthored field as a chip that enters edit mode
 * with that field focused. Empty is information, not a blank space.
 */
export interface GapChipsProps {
  /** Default "Gaps to review". */
  label?: string;
  /** Field names, or [value, label] pairs. */
  items?: (string | [string, string])[];
  onPick?: (value: string) => void;
  /** The dashed top rule that detaches the band. Default true. */
  dashed?: boolean;
  style?: React.CSSProperties;
}
export declare function GapChips(props: GapChipsProps): JSX.Element;
