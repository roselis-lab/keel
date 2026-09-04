import * as React from "react";

/** A white card on a tint band. Depth comes from inverting the fill, never a shadow. */
export interface CardProps {
  /** Mono secondary — the entity id. */
  id?: string;
  /** 14px/600 primary line. */
  title?: string;
  /** Italic muted line — why this control addresses this threat. */
  rationale?: string;
  /** Regular muted line, pre-wrap. */
  desc?: string;
  /** Badges rendered inline after the title. */
  badges?: React.ReactNode;
  /** Marks the card as a jump target: crimson-50 hover + crimson-200 border. */
  jump?: boolean;
  onClick?: () => void;
  children?: React.ReactNode;
  style?: React.CSSProperties;
}
export declare function Card(props: CardProps): JSX.Element;
