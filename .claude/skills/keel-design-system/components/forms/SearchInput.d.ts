import * as React from "react";

/** The left-rail text filter. Includes its own 10px 14px row and bottom hairline. */
export interface SearchInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  /** Sentence case with an ellipsis, e.g. "Filter threats…". */
  placeholder?: string;
}
export declare function SearchInput(props: SearchInputProps): JSX.Element;
