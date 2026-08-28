import React from "react";

const TONES = {
  soft:   { bg: "var(--navy-100)", fg: "var(--navy-600)", weight: "var(--fw-medium)", radius: "var(--r-pill)" },
  type:   { bg: "var(--navy-200)", fg: "var(--navy-700)" },
  harm:   { bg: "var(--crimson-600)", fg: "#fff" },
  danger: { bg: "var(--crimson-50)", fg: "var(--crimson-700)" },
  ok:     { bg: "var(--green-50)", fg: "var(--green)" },
  advice: { bg: "var(--amber-50)", fg: "var(--amber)" },
  orphan: { bg: "var(--navy-200)", fg: "var(--navy-600)" },
};

/** A word in a coloured pill. Keel says the word rather than drawing a symbol. */
export function Badge({ tone = "soft", numeric, mono, children, style, ...rest }) {
  const t = TONES[tone] || TONES.soft;
  return (
    <span
      style={{
        fontSize: "var(--fs-10)", padding: "1px 8px",
        borderRadius: t.radius || "var(--r-4)",
        fontWeight: t.weight || "var(--fw-semibold)",
        whiteSpace: "nowrap", background: t.bg, color: t.fg,
        fontFamily: mono ? "var(--font-mono)" : "var(--font-sans)",
        fontVariantNumeric: numeric ? "var(--numeric)" : "normal",
        ...style,
      }}
      {...rest}
    >
      {children}
    </span>
  );
}
