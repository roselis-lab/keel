import * as React from "react";

/**
 * The product's only button. One crimson primary per screen; everything else is ghost.
 * @startingPoint section="Core" subtitle="Primary, ghost and bare buttons at both sizes" viewport="700x150"
 */
export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  /** primary = crimson fill (one per screen). ghost = navy-100 fill. bare = no fill until hover. */
  variant?: "primary" | "ghost" | "bare";
  /** md = 7px 13px / 13px. sm = 4px 9px / 12px. */
  size?: "md" | "sm";
  disabled?: boolean;
  /** A Unicode glyph rendered before the label, e.g. "\uFF0B" for New. Never an icon component. */
  glyph?: string;
  children?: React.ReactNode;
}
export declare function Button(props: ButtonProps): JSX.Element;
