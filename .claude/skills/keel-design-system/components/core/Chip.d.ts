import * as React from "react";

/** Multi-select filter chip (facet) or clickable jump-to-entity chip. */
export interface ChipProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  /** Selected = solid crimson-600 fill, white text. */
  selected?: boolean;
  /** facet = 11px pill in a filter group. jump = 12px mono 6px-radius chip that navigates. */
  variant?: "facet" | "jump";
  mono?: boolean;
  children?: React.ReactNode;
}
export declare function Chip(props: ChipProps): JSX.Element;
