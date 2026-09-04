import * as React from "react";

export interface FacetGroup {
  /** State key, e.g. "harm", "surface", "component". */
  key: string;
  /** Sentence-case group heading, uppercased by CSS at 10px. */
  label: string;
  /** Enum values, or [value, label] pairs. Sourced from the JSON Schema, never hardcoded. */
  options: (string | [string, string])[];
}

/** The rail's multi-select filter: collapsed to "Filters (N)" until opened. */
export interface FacetPanelProps {
  groups?: FacetGroup[];
  /** { groupKey: selectedValues[] }. */
  selected?: Record<string, string[]>;
  open?: boolean;
  /** Total selected chips across all groups — drives the crimson count badge. */
  activeCount?: number;
  onOpen?: (open: boolean) => void;
  onToggle?: (groupKey: string, value: string) => void;
  onClear?: () => void;
  style?: React.CSSProperties;
}
export declare function FacetPanel(props: FacetPanelProps): JSX.Element;
