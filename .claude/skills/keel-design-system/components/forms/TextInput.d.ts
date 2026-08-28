import * as React from "react";

/** The single-line text control: 38px min-height, 8px radius, crimson focus ring. */
export interface TextInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  /** Tint the resting border crimson-200 when the field failed validation. */
  invalid?: boolean;
  /** Mono stack — use for id fields and reference URLs. */
  mono?: boolean;
  /** Render as the inline entity-title input: 19px / 700. */
  title?: boolean;
}
export declare function TextInput(props: TextInputProps): JSX.Element;
