import { Fragment, type ReactNode } from "react";
import type { Level } from "./types";

export const ORDER: Record<Level, number> = { high: 0, medium: 1, low: 2 };
export const cap = (s?: string | null) => (s ? s.charAt(0).toUpperCase() + s.slice(1) : "");
export const firstSentence = (t?: string | null) => {
  const s = String(t || "");
  const m = s.match(/^(.+?[.!?])(\s|$)/);
  return m ? m[1] : s;
};
/** A short title for a fix written as a paragraph: up to the first colon, dash or full stop. */
export const shortTitle = (t?: string | null, max = 90) => {
  const s = firstSentence(t).replace(/[.]$/, "");
  const cut = s.search(/[:;—]| - /);
  return clip(cut > 24 ? s.slice(0, cut) : s, max);
};
/** What a tracked source is. Compliance is asked of the first two only. */
export const KIND: Record<"regulation" | "standard" | "best_practice", { one: string; many: string }> = {
  regulation: { one: "Regulation", many: "Regulations" },
  standard: { one: "Standard", many: "Standards" },
  best_practice: { one: "Best practice", many: "Best practice" },
};
export const KINDS = ["regulation", "standard", "best_practice"] as const;
export const clip = (t: string, n: number) => (t.length > n ? t.slice(0, n).replace(/\s+\S*$/, "") + "…" : t);
export const plural = (n: number, one: string, many = one + "s") => `${n} ${n === 1 ? one : many}`;

export const HARM: Record<string, string> = {
  "data-integrity": "Data integrity", "wrong-decision": "Wrong decision", "reputation-legal": "Reputation or legal", downtime: "Downtime",
  "data-exposed": "Data exposed", "code-execution": "Code execution", "privilege-escalation": "Privilege escalation",
  "resource-abuse": "Resource abuse", "financial-loss": "Financial loss",
};
export const SURF: Record<string, string> = {
  "model-output": "Model output", "retrieved-content": "Retrieved content", memory: "Memory", "user-input": "User input",
  "tool-output": "Tool output", "agent-message": "Agent message",
};
export const WHO: Record<string, string> = {
  internal: "Insider or user", insider: "Insider or user", "model-overreach": "Overreaching model", "external-attacker": "External attacker",
  "supply-chain": "Supply chain", "model-goal": "The model's own goal", "model-mistake": "Model mistake", "model-overeager": "Overeager model",
  error: "Error", accident: "Accident",
};
export const CLASS: Record<string, string> = {
  gating_control: "Stops it", detector: "Detects it", process: "Process", evidential_mitigation: "Keeps evidence", corrective: "Repairs after",
};
export const STATUS: Record<string, string> = { needs_implementation: "Not built", partial: "Partly in place", already_covered: "In place" };
export const failText = (v?: string) => ({ fail_closed: "Fails closed", fail_open: "Fails open" } as Record<string, string>)[v || ""] || cap(String(v || "").replace(/_/g, " "));
export const harmLabel = (h?: string) => HARM[h || ""] || cap(h || "");

/* ---- a small markdown: paragraphs, bullet lists, pipe tables, **bold**, `code` ----
   Catalog prose uses no more than this. Built as React elements, never as HTML strings. */
function inline(s: string): ReactNode[] {
  const out: ReactNode[] = [];
  const re = /\*\*(.+?)\*\*|`([^`]+)`/g;
  let last = 0, m: RegExpExecArray | null, k = 0;
  while ((m = re.exec(s))) {
    if (m.index > last) out.push(s.slice(last, m.index));
    out.push(m[1] !== undefined ? <b key={k++}>{m[1]}</b> : <code key={k++}>{m[2]}</code>);
    last = re.lastIndex;
  }
  if (last < s.length) out.push(s.slice(last));
  return out;
}
export function Md({ text }: { text?: string | null }) {
  if (!text) return null;
  const blocks: ReactNode[] = [];
  let para: string[] = [], list: string[] | null = null, table: string[] | null = null, k = 0;
  const flushP = () => { if (para.length) blocks.push(<p key={k++}>{inline(para.join(" "))}</p>); para = []; };
  const flushL = () => { if (list) blocks.push(<ul key={k++}>{list.map((x, i) => <li key={i}>{inline(x)}</li>)}</ul>); list = null; };
  const flushT = () => {
    if (!table) return;
    const rows = table.filter((r) => !/^\s*\|?\s*:?-{2,}/.test(r));
    const cells = (r: string) => r.replace(/^\s*\||\|\s*$/g, "").split("|").map((c) => c.trim());
    const [h, ...body] = rows;
    blocks.push(<table key={k++}><thead><tr>{cells(h).map((c, i) => <th key={i}>{inline(c)}</th>)}</tr></thead>
      <tbody>{body.map((r, i) => <tr key={i}>{cells(r).map((c, j) => <td key={j}>{inline(c)}</td>)}</tr>)}</tbody></table>);
    table = null;
  };
  for (const l of String(text).split("\n")) {
    if (/^\s*\|/.test(l)) { flushP(); flushL(); (table ||= []).push(l); continue; } else flushT();
    if (/^\s*[-*] /.test(l)) { flushP(); (list ||= []).push(l.replace(/^\s*[-*] /, "")); continue; }
    if (/^\s+\S/.test(l) && list) { list[list.length - 1] += " " + l.trim(); continue; }
    if (!l.trim()) { flushP(); flushL(); continue; }
    flushL(); para.push(l.trim());
  }
  flushP(); flushL(); flushT();
  return <div className="md">{blocks}</div>;
}
/** Inline marks only, for one-line fields that may carry **bold** or `code`. */
export const Inl = ({ text }: { text?: string | null }) => <Fragment>{inline(String(text || ""))}</Fragment>;
