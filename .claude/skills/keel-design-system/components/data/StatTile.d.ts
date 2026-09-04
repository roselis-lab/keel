import * as React from "react";

/**
 * One count on the Overview: threats, mitigations, links, systems assessed.
 * @startingPoint section="Data" subtitle="Overview counts, coverage bars and split bars" viewport="700x230"
 */
export interface StatTileProps {
  value: string | number;
  /** Sentence case, plural noun: "threats", "mitigation links". */
  label: string;
  style?: React.CSSProperties;
}
export declare function StatTile(props: StatTileProps): JSX.Element;
