import * as React from "react";

/** Multi-value enum fields as a wrapping row of white checkbox capsules. */
export interface CheckSetProps {
  /** Enum values, or [value, label] pairs. */
  options?: (string | [string, string])[];
  /** The currently checked values. */
  value?: string[];
  onToggle?: (value: string) => void;
  style?: React.CSSProperties;
}
export declare function CheckSet(props: CheckSetProps): JSX.Element;
