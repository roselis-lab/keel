import * as React from "react";

/** The post-write receipt. Keel writes YAML, not commits — this points at the file to commit. */
export interface SavedDialogProps {
  /** The catalog path written, e.g. "catalog/threats/T-TOOL-ABUSE.yaml". */
  file?: string;
  message?: string;
  show?: boolean;
  /** Optional repo link; omitted when /config returns an empty repo_url. */
  repoUrl?: string;
  onClose?: () => void;
  style?: React.CSSProperties;
}
export declare function SavedDialog(props: SavedDialogProps): JSX.Element;
