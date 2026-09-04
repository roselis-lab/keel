import * as React from "react";

/** A collapsible repeatable form record: weaknesses, mitigation links, references, implementations. */
export interface EditorCardProps {
  /** Mono one-line summary shown collapsed, e.g. "tool · targeted". */
  summary: string;
  open?: boolean;
  /** Shows a crimson dot and tints the border when collapsed over an errored field. */
  hasError?: boolean;
  onToggle?: () => void;
  /** Omit to hide the × remove control. */
  onRemove?: () => void;
  children?: React.ReactNode;
  style?: React.CSSProperties;
}
export declare function EditorCard(props: EditorCardProps): JSX.Element;
