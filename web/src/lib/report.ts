import type { Finding, Level, Mitigation, Report, Requirement, Threat } from "./types";
import { ORDER, shortTitle, firstSentence } from "./text";

/** A finding's title: the library threat's sentence, or the first sentence of its weak spot. */
export const findingTitle = (f: Finding, threats: Record<string, Threat>) =>
  threats[f.id]?.title || firstSentence(f.vulnerability);

export interface Fix {
  key: string;
  id: string | null;             // library control id, or null for a fix written for this system
  title: string;                 // short: what the developer reads in a list
  text: string | null;           // the full ask, for a fix that is not a library card
  status: Requirement["coverage_status"];
  risks: Finding[];
  reqs: Requirement[];
}

export const reqKey = (q: Requirement) => q.mitigation_id || "ask:" + (q.description || "").slice(0, 80);

export interface Prepared {
  findings: Finding[];
  fixes: Fix[];                  // every fix once, with the risks it closes
  open: Fix[];                   // fixes not yet in place
  first: Fix[];                  // the fixes that close every high-severity risk
  count: (s: Level) => number;
  minutes: number | null;
}

/** Everything a report page derives from a report, by code: order, the fix list, what to do first. */
export function prepare(r: Report, mits: Record<string, Mitigation>): Prepared {
  const findings = [...r.findings].sort((a, b) =>
    ORDER[a.risk.severity] - ORDER[b.risk.severity] || ORDER[a.risk.likelihood] - ORDER[b.risk.likelihood]);
  const m = new Map<string, Fix>();
  for (const f of findings) for (const q of f.requirements) {
    if (!q.included && q.coverage_status !== "already_covered") continue;
    const key = reqKey(q);
    const e = m.get(key) || {
      key, id: q.mitigation_id,
      title: q.mitigation_id ? mits[q.mitigation_id]?.name || q.mitigation_id : shortTitle(q.description),
      text: q.mitigation_id ? null : q.description,
      status: q.coverage_status, risks: [], reqs: [],
    };
    if (!e.risks.includes(f)) e.risks.push(f);
    e.reqs.push(q);
    m.set(key, e);
  }
  const fixes = [...m.values()].sort((a, b) =>
    b.risks.length - a.risks.length || ORDER[a.risks[0].risk.severity] - ORDER[b.risks[0].risk.severity]);
  const open = fixes.filter((x) => x.status !== "already_covered");
  // A risk closes only when all of its fixes are in, so "first" is every open fix of every
  // high-severity risk, not a cover that touches each one once.
  const high = findings.filter((f) => f.risk.severity === "high");
  const first = open.filter((x) => x.risks.some((f) => high.includes(f)));
  const minutes = r.meta.started_at && r.meta.finished_at
    ? Math.round((+new Date(r.meta.finished_at) - +new Date(r.meta.started_at)) / 60000) : null;
  return { findings, fixes, open, first, minutes, count: (s) => findings.filter((f) => f.risk.severity === s).length };
}

export const backing = (f: Finding) => (f.review ? "tested" : (f.evidence || []).length ? "evidence" : "unchecked") as "tested" | "evidence" | "unchecked";
export const BACKING = { tested: "Survived review", evidence: "Evidence attached", unchecked: "Unchecked" };
export const assessorName = (a: string) => a.split("<")[0].trim();
export const reportPath = (r: Report) => `reports/${r.system_id}/${r.date}.yaml`;
