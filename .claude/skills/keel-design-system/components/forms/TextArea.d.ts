import * as React from "react";

/** The multi-line prose control. Vertically resizable only. */
export interface TextAreaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  invalid?: boolean;
  /** Default 4. */
  rows?: number;
}
export declare function TextArea(props: TextAreaProps): JSX.Element;
