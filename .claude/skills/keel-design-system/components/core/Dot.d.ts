import * as React from "react";

/** An 8px status circle — hung off a section label, or used as a bar-chart legend key. */
export interface DotProps extends React.HTMLAttributes<HTMLSpanElement> {
  /** error = crimson (blocks), advice = amber (never blocks), ok = green, none = navy-200. */
  tone?: "error" | "advice" | "ok" | "none";
  /** Pixel diameter. 8 in the field-error marker, 8 in the legend. */
  size?: number;
}
export declare function Dot(props: DotProps): JSX.Element;
