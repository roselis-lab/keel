import * as React from "react";

/** A one-line inline caveat inside a read view or a dashboard panel. */
export interface WarnBannerProps {
  /** error = crimson wash. ok = green wash (the "nothing to review" state). */
  tone?: "error" | "ok";
  children?: React.ReactNode;
  style?: React.CSSProperties;
}
export declare function WarnBanner(props: WarnBannerProps): JSX.Element;
