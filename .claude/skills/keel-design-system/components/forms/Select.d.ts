import * as React from "react";

/** A fixed-vocabulary dropdown. In Keel the options are read from the JSON Schema. */
export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  invalid?: boolean;
  /** Enum values, or [value, label] pairs. Keep values verbatim and lowercase. */
  options?: (string | [string, string])[];
  /** Adds a leading empty option, e.g. "— select a harm —". */
  placeholder?: string;
}
export declare function Select(props: SelectProps): JSX.Element;
