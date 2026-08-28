import * as React from "react";

/** The type / id line above a read view, with the optional git provenance line under it. */
export interface BreadcrumbProps {
  /** "Threats" or "Mitigations" — clickable, returns to the list. */
  type: string;
  /** Mono id. */
  id: string;
  onType?: () => void;
  /** Sentence-case provenance, e.g. "Last changed 2 days ago by jane". */
  lastChanged?: string;
  /** Reveals the latest diff inline. */
  onViewChange?: () => void;
  style?: React.CSSProperties;
}
export declare function Breadcrumb(props: BreadcrumbProps): JSX.Element;
