import * as React from "react";

export interface SplitBarSegment {
  /** verified/shared/ok = green. draft/local = amber. unset/none = navy-200. */
  tone: "verified" | "shared" | "ok" | "draft" | "local" | "unset" | "none";
  /** Sentence-case lowercase noun: "verified", "draft", "no implementations". */
  label: string;
  value: number;
}

/** A 10px proportional bar with a dot legend beneath. Widths are computed from the values. */
export interface SplitBarProps {
  segments?: SplitBarSegment[];
  style?: React.CSSProperties;
}
export declare function SplitBar(props: SplitBarProps): JSX.Element;
