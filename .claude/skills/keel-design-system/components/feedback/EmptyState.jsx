import React from "react";

/** One line of navy-400 text. Keel ships no empty-state art. */
export function EmptyState({ children, top = "22vh", style }) {
  return (
    <div style={{
      color: "var(--navy-400)", marginTop: top, textAlign: "center",
      fontFamily: "var(--font-sans)", fontSize: "var(--fs-14)", ...style,
    }}>{children}</div>
  );
}
