import * as React from "react";

/** The top-of-rail screen switcher: Overview · Threats · Mitigations · Style guide · Reports. */
export interface ScreenTabsProps {
  /** Values, or [value, label] pairs. Labels are sentence case. */
  screens?: (string | [string, string])[];
  value?: string;
  onChange?: (value: string) => void;
  style?: React.CSSProperties;
}
export declare function ScreenTabs(props: ScreenTabsProps): JSX.Element;
