// The shapes the Keel API returns. Only the fields the app reads are named; the API
// is the source of truth (keel/schemas/*.py).
export type Level = "low" | "medium" | "high";
export type CoverageStatus = "already_covered" | "needs_implementation" | "partial";

export interface Requirement {
  mitigation_id: string | null;
  description: string | null;
  coverage_status: CoverageStatus;
  coverage_note: string | null;
  included: boolean;
  invariant?: string | null;
  enforce_at?: string | null;
  done_check?: string | null;
}
export interface Finding {
  id: string;
  from_catalog: boolean;
  scenario: string;
  source: { who: string; motive: string; access: string };
  asset: string;
  attack_surface: string | null;
  vulnerability: string;
  exploitation_complexity: Level;
  harm: string;
  risk: { likelihood: Level; severity: Level; reasoning: string };
  risk_today?: { likelihood: Level; severity: Level; reasoning: string } | null;
  delta: string;
  origin?: "new" | "changed" | "legacy" | null;
  deployment?: string | null;
  root_cause?: string | null;
  evidence?: number[];
  review?: { by: string; verdict: string; note: string } | null;
  requirements: Requirement[];
  ignored_mitigations?: { mitigation_id: string; reason: string }[];
}
export interface Evidence { id: number; kind: "read" | "command" | "test"; quote: string; commit?: string; path?: string; lines?: string; url?: string; command?: string }
export interface OpenQuestion { id: string; question: string; asks_for: string; looked_in: string; needed_for: string; how_to_check: string; answer?: string | null }
export interface Surface { id: string; kind: "entry" | "tool" | "data" | "file"; name: string; where: string; outcome: string[]; note?: string | null; found_by?: string }
export interface Report {
  system_id: string;
  system_name: string;
  system_description: string;
  date: string;
  assessor: string;
  status: "draft" | "final";
  delta_summary?: string | null;
  findings: Finding[];
  discarded: { id: string; by: "reachability" | "review"; reason: string }[];
  paused?: { id: string; from_catalog: boolean; waiting_on: string[]; note: string }[];
  surfaces?: Surface[];
  open_questions?: OpenQuestion[];
  evidence?: Evidence[];
  meta: { started_at?: string | null; finished_at?: string | null; questions: { question: string; answer: string; impact: string }[]; volunteered: string[] };
}
export interface SystemRow { system_id: string; system_name: string; latest_date: string; status: string; report_count: number; has_delta: boolean }

export interface ThreatLink { id: string; strength: "gating" | "soft"; rationale: string }
export interface Threat {
  id: string;
  title: string;
  harm: string;
  source: string[];
  weaknesses: { component: string; surface?: string[]; text: string; nature?: string }[];
  reachability?: string;
  references?: { title: string; url: string; note: string }[];
  positioning?: string;
  mitigations: ThreatLink[];
  cited_by?: { source_id: string; source_title: string; ref: string; title: string }[];
}
export interface Mitigation {
  id: string;
  name: string;
  mitigation_class: string;
  purpose?: string;
  formal_implementation_risk?: string;
  locus?: { value: string; note: string } | null;
  scope?: string;
  out_of_scope?: string;
  control_mechanism?: string;
  failure_behavior?: { value: string; note: string } | null;
  telemetry?: { events: { name: string; records: string; attributes: string[] }[]; evidence: string } | null;
  anti_patterns?: string[];
  validation?: { criterion: string; base?: boolean }[];
  faq?: { question: string; answer: string }[];
  requires?: string[];
  cited_by?: { source_id: string; source_title: string; ref: string; title: string }[];
}

export interface CoverageEntry { ref: string; title: string; group?: string | null; state: "covered" | "out_of_scope" | "gap"; threats?: string[]; mitigations?: string[]; note?: string | null; outside?: string | null }
export type SourceKind = "regulation" | "standard" | "best_practice";
export interface CoverageSource {
  source: { id: string; title: string; kind: SourceKind; version: string; checked: string; url?: string; note?: string; entry_count?: number };
  counts: { covered: number; out_of_scope: number; gap: number };
  entries: CoverageEntry[];
}

export type Standing = "not_met" | "waiting" | "not_assessed" | "met" | "does_not_apply" | "out_of_scope" | "library_gap";
export interface ThreatStanding { threat: string; standing: Standing; why?: string | null; severity?: Level; likelihood?: Level; open_fixes?: number; waiting_on?: string[] }
export interface ComplianceFramework {
  source: CoverageSource["source"];
  counts: Record<Standing, number>;
  entries: { ref: string; title: string; group?: string | null; standing: Standing; threats: ThreatStanding[]; note?: string | null; outside?: string | null }[];
}
export interface SystemCompliance { system_id: string; system_name: string; date: string; status: string; frameworks: ComplianceFramework[] }
export interface AllCompliance {
  frameworks: CoverageSource["source"][];
  systems: { system_id: string; system_name: string; date: string; status: string; frameworks: { source_id: string; counts: Record<Standing, number> }[] }[];
}
