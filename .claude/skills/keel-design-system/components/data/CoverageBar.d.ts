import * as React from "react";

/** A style-guide coverage row. Grades itself: >=80 green, >=40 amber, below that crimson. */
export interface CoverageBarProps {
  /** The field or entity name, rendered mono. */
  label: string;
  /** 0-100. Ignored when `orphan` is set. */
  percent: number;
  /** Guidance exists but no matching model field — renders a navy "orphan" badge. */
  orphan?: boolean;
  style?: React.CSSProperties;
}
export declare function CoverageBar(props: CoverageBarProps): JSX.Element;
