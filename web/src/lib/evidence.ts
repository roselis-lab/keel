/* Evidence marks in report prose. Plain text work, no React, so `npm test` runs it
   under Node (web/test/evidence.test.ts).

   A claim points at its evidence with a marker (keel/schemas/report.py, Evidence): `[3]`,
   a list `[1, 3]`, a link written `[the refund call](#ev-3)`, or a bare `#ev-3`. */

import type { Evidence } from "./types";

export type Segment = { text: string; id?: undefined } | { id: number; label: string; broken: boolean };

const MARK = new RegExp(
  [
    String.raw`\[([^\]\n]{1,200}?)\]\(#ev-(\d{1,6})\)`, // [text](#ev-3)
    String.raw`(?<![\w\]])\[(\d{1,6}(?:\s*,\s*\d{1,6})*)\]`, // [3] or [1, 3]; not items[3]
    String.raw`(?<![\w/#-])#ev-(\d{1,6})(?![\w-])`, // #ev-3
  ].join("|"),
  "g",
);

/** The text cut into plain text and marks, in order. A mark whose number `ids` does not
    hold is `broken`. A link `[words](#ev-3)` is labelled by its words; any other mark
    keeps its own text, so the plain text and labels joined read as the prose did. */
export function splitMarks(text: string, ids: { has(id: number): boolean }): Segment[] {
  const out: Segment[] = [];
  const plain = (t: string) => {
    if (!t) return;
    const last = out[out.length - 1];
    if (last && last.id === undefined) last.text += t;
    else out.push({ text: t });
  };
  const mark = (id: number, label: string) => out.push({ id, label, broken: !ids.has(id) });
  let last = 0;
  for (const m of text.matchAll(MARK)) {
    plain(text.slice(last, m.index!));
    if (m[2] !== undefined) mark(Number(m[2]), m[1]);
    else if (m[4] !== undefined) mark(Number(m[4]), m[0]);
    else {
      const parts = m[3].split(/(\s*,\s*)/); // numbers at even places, separators between
      if (parts.length === 1) mark(Number(parts[0]), m[0]);
      else {
        plain("[");
        parts.forEach((p, i) => (i % 2 ? plain(p) : mark(Number(p), p)));
        plain("]");
      }
    }
    last = m.index! + m[0].length;
  }
  plain(text.slice(last));
  return out;
}

/** A quote short enough for a tooltip: at most `lines` lines and `chars` characters,
    line breaks kept, an ellipsis on its own line where it was cut. */
export function clipQuote(quote: string, lines = 8, chars = 420): string {
  const s = String(quote || "").replace(/\r\n?/g, "\n").replace(/^\n+|\s+$/g, "");
  const rows = s.split("\n");
  let cut = rows.length > lines;
  let t = rows.slice(0, lines).join("\n");
  if (t.length > chars) {
    t = t.slice(0, chars).replace(/\s+\S*$/, "");
    cut = true;
  }
  return cut ? t + "\n…" : t;
}

/** Where the evidence is, for the lines under the quote: `path:lines`, then the
    repository and the short commit. A command or a test says what was run. */
export function whereLines(e: Evidence): string[] {
  if (e.kind !== "read") return [`${e.kind}: ${e.command || ""}`.trim()];
  const out = [e.lines ? `${e.path}:${e.lines}` : String(e.path || "")];
  const at = [e.repo, e.commit ? e.commit.slice(0, 7) : null].filter(Boolean).join(" @ ");
  if (at) out.push(at);
  return out;
}
