import * as React from "react";

/** A bare Unicode glyph in a small hit area. Keel has no icon set — pass a glyph character. */
export interface IconButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  /** One Unicode character: "«" "»" "▾" "▸" "×" "＋". Never an emoji, never an SVG. */
  glyph: string;
  /** danger tints the hover state crimson (used by the remove-card ×). */
  tone?: "neutral" | "danger";
  /** Required — becomes both title and aria-label. */
  title: string;
}
export declare function IconButton(props: IconButtonProps): JSX.Element;
