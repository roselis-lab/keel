import { useState } from "react";
import { Link, useParams } from "react-router";
import { THREATS, useApi } from "../lib/api";
import type { AllCompliance, ComplianceFramework, CoverageSource, SourceKind, Standing, SystemCompliance, Threat } from "../lib/types";
import { clip, KIND, plural } from "../lib/text";
import { Head, Legend, Loading, Problem, Shell, Stack, Toggle } from "../components/ui";
import { byId } from "./Report";

export const STANDING: Record<Standing, string> = {
  not_met: "Not met", waiting: "Waiting on an answer", not_assessed: "Not assessed", met: "Met",
  does_not_apply: "Does not apply", out_of_scope: "Outside the library", library_gap: "No library card yet",
};
const ORDER: Standing[] = ["not_met", "waiting", "not_assessed", "met", "does_not_apply", "library_gap", "out_of_scope"];
const parts = (c: Record<Standing, number>) => ORDER.map((k) => [k, c[k] || 0] as [string, number]);
const total = (c: Record<Standing, number>) => ORDER.reduce((a, k) => a + (c[k] || 0), 0);
const inReach = (c: Record<Standing, number>) => total(c) - (c.out_of_scope || 0) - (c.library_gap || 0);
// "No card yet" and "outside the library" share a swatch: both are beyond what an assessment can reach.
const LegendAll = ({ c }: { c?: Record<Standing, number> }) => <Legend items={ORDER.filter((k) => k !== "library_gap" && (!c || (c[k] || 0) + (k === "out_of_scope" ? c.library_gap || 0 : 0) > 0)).map((k) =>
  k === "out_of_scope" ? [k, "Beyond the library", c ? (c.out_of_scope || 0) + (c.library_gap || 0) : undefined] : [k, STANDING[k], c ? c[k] || 0 : undefined])} />;

type Source = CoverageSource["source"];
const binding = (k: SourceKind) => k !== "best_practice";

const LEDE = <p className="lede quiet">Where each assessed system stands, worked out from its latest assessment: first against regulations and standards, then against best-practice threat lists. Falling short of best practice is a finding, not a breach.</p>;
const HOW = <details className="det" style={{ maxWidth: "80ch", marginBottom: 20 }}><summary>How this is worked out</summary><p className="prose">Each entry of a regulation, standard or framework is matched to the library's threats, and each threat to what this assessment found. An entry is <b>met</b> when every threat behind it is closed or does not apply to the system, and <b>not met</b> while any of them is an open risk. Entries the library does not model are shown apart and never counted against the system.</p></details>;
// What it takes to add the first one, said where the reader looks for it, instead of an empty table.
const NONE_BINDING = <div className="empty" style={{ textAlign: "left", maxWidth: "80ch" }}><b>No regulation or standard is tracked yet</b>One is added the way the frameworks below were: a coverage file under <code>catalog/coverage</code> with <code>kind: regulation</code> or <code>kind: standard</code>, mapping each article to the threats it asks a system to handle. The library side shows on <Link to="/coverage">Coverage</Link>.</div>;

function Matrix({ fws, systems }: { fws: Source[]; systems: AllCompliance["systems"] }) {
  return <table className="tbl matrix"><thead><tr><th>System</th>{fws.map((f) => <th key={f.id}>{f.title}</th>)}</tr></thead><tbody>
    {systems.map((s) => <tr key={s.system_id}>
      <td><Link className="rlink" to={`/compliance/${s.system_id}`}>{s.system_name}</Link><div className="t3 small">{s.date} · {s.status}</div></td>
      {fws.map((fw) => {
        const c = s.frameworks.find((x) => x.source_id === fw.id)!.counts;
        return <td key={fw.id} className="cellbar" data-l={fw.title}>
          <Link to={`/compliance/${s.system_id}?f=${fw.id}`} style={{ textDecoration: "none" }}>
            <Stack parts={parts(c)} total={total(c)} label={`${c.not_met || 0} not met of ${total(c)}`} />
            <span className="small"><b style={{ color: c.not_met ? "var(--hi)" : undefined }}>{c.not_met || 0} of {inReach(c)} not met</b></span>
          </Link></td>;
      })}
    </tr>)}
  </tbody></table>;
}

export function ComplianceAll() {
  const q = useApi<[AllCompliance]>("/compliance");
  if (q.loading) return <Shell title="Compliance"><Loading /></Shell>;
  if (q.error) return <Shell title="Compliance"><Problem error={q.error} what="compliance" /></Shell>;
  const d = q.data[0];
  const law = d.frameworks.filter((f) => binding(f.kind)), bp = d.frameworks.filter((f) => !binding(f.kind));
  return (
    <Shell title="Compliance">
      <Head title="Compliance" meta={[plural(d.systems.length, "system"), law.length ? plural(law.length, "regulation or standard", "regulations and standards") : "No regulation tracked yet", plural(bp.length, "best-practice framework")]} lede={LEDE} />
      {HOW}
      {d.systems.length === 0 ? <div className="empty"><b>No assessments yet</b>Assess a system and its standing appears here.</div> : <>
        <section><h2>Regulations and standards</h2>{law.length ? <><LegendAll /><Matrix fws={law} systems={d.systems} /></> : NONE_BINDING}</section>
        {bp.length > 0 && <section><h2>Best practice</h2><p className="sub">Threat lists with no force of their own. How far a system is from them shows what to work on.</p><LegendAll /><Matrix fws={bp} systems={d.systems} /></section>}
      </>}
    </Shell>
  );
}

function Framework({ fw, threats, sid, date }: { fw: ComplianceFramework; threats: Record<string, Threat>; sid: string; date: string }) {
  const [order, setOrder] = useState<"problems" | "list">("problems");
  const c = fw.counts;
  const rows = order === "problems" ? [...fw.entries].sort((a, b) => ORDER.indexOf(a.standing) - ORDER.indexOf(b.standing)) : fw.entries;
  return (
    <section id={fw.source.id}>
      <h2>{fw.source.title} <span className="tag" style={{ marginLeft: 6 }}>{KIND[fw.source.kind]?.one}</span></h2>
      <p className="sub">{total(c)} entries: <b style={{ color: c.not_met ? "var(--hi)" : "var(--ink)" }}>{c.not_met || 0} not met</b>{c.met ? `, ${c.met} met` : ""}{c.does_not_apply ? `, ${c.does_not_apply} do not apply` : ""}{c.waiting ? `, ${c.waiting} waiting on an answer` : ""}{c.not_assessed ? `, ${c.not_assessed} not assessed` : ""}{(c.out_of_scope || 0) + (c.library_gap || 0) ? `, ${(c.out_of_scope || 0) + (c.library_gap || 0)} beyond what the library covers` : ""}. <span className="t3">Version {fw.source.version}.</span></p>
      <Stack big parts={parts(c)} total={total(c)} label={`${c.not_met || 0} not met`} />
      <LegendAll c={c} />
      <Toggle label="Order" value={order} onChange={setOrder} options={[["problems", "Not met first"], ["list", "In framework order"]]} />
      <table className="tbl"><thead><tr><th style={{ width: 90 }}>Entry</th><th>Name</th><th style={{ width: 170 }}>Standing</th><th>Why</th></tr></thead><tbody>
        {rows.map((e) => <tr key={e.ref}>
          <td><span className="id">{e.ref}</span></td>
          <td><b style={{ fontWeight: 600 }}>{e.title}</b></td>
          <td data-l="Standing"><span className={`st ${e.standing}`}><i className={`k-${e.standing}`} />{STANDING[e.standing]}</span></td>
          <td data-l="Why" className="small">
            {e.threats.length === 0 && <span className="t2">{e.standing === "not_assessed" ? "The library answers this with a control and no threat, so an assessment does not reach it." : e.note || STANDING[e.standing] + "."}</span>}
            {e.threats.map((t) => <div key={t.threat} style={{ marginBottom: 6 }}>
              <span className={`st ${t.standing}`} style={{ fontWeight: 600 }}><i className={`k-${t.standing}`} /></span>{" "}
              {t.standing === "not_met" || t.standing === "met"
                ? <Link to={`/reports/${sid}/${date}/${t.threat}`}>{clip(threats[t.threat]?.title || t.threat, 90)}</Link>
                : <Link to={`/threats/${t.threat}`}>{clip(threats[t.threat]?.title || t.threat, 90)}</Link>}
              <span className="t2"> — {t.standing === "not_met" ? `${t.severity} risk, ${plural(t.open_fixes || 0, "fix", "fixes")} not built` : t.standing === "met" ? "every fix in place" : t.standing === "not_assessed" ? "not looked at in this assessment" : clip(t.why || "", 180)}</span>
            </div>)}
          </td>
        </tr>)}
      </tbody></table>
    </section>
  );
}

export function ComplianceSystem() {
  const { system } = useParams();
  const q = useApi<[SystemCompliance, { threats: Threat[] }, AllCompliance]>(`/compliance/${system}`, THREATS, "/compliance");
  const pick = new URLSearchParams(location.search).get("f");
  const [cur, setCur] = useState<string | null>(pick);
  if (q.loading) return <Shell title="Compliance"><Loading /></Shell>;
  if (q.error) return <Shell title="Compliance"><Problem error={q.error} what="compliance" /></Shell>;
  const [d, t, all] = q.data;
  const threats = byId(t.threats);
  const fw = d.frameworks.find((f) => f.source.id === cur) || d.frameworks[0];
  const item = (f: ComplianceFramework) => (
    <button key={f.source.id} className="item" aria-current={f.source.id === fw.source.id ? "page" : undefined} onClick={() => setCur(f.source.id)}>
      <b>{f.source.title}</b><span>{f.counts.not_met || 0} of {inReach(f.counts)} not met</span>
      <Stack parts={parts(f.counts)} total={total(f.counts)} label={`${f.counts.not_met || 0} not met`} />
    </button>);
  const law = d.frameworks.filter((f) => binding(f.source.kind)), bp = d.frameworks.filter((f) => !binding(f.source.kind));
  const rail = <><h2>Regulations and standards</h2>{law.length ? law.map(item) : <p className="t3 small" style={{ padding: "4px 0" }}>None tracked yet.</p>}
    <h2 style={{ marginTop: 22 }}>Best practice</h2>{bp.map(item)}
    <h2 style={{ marginTop: 22 }}>Systems</h2>{all.systems.map((s) => <Link key={s.system_id} className="item" to={`/compliance/${s.system_id}`} aria-current={s.system_id === d.system_id ? "page" : undefined}><b>{s.system_name}</b></Link>)}</>;
  return (
    <Shell title={`${d.system_name} compliance`} rail={rail}>
      <Link className="back-s" to="/compliance">← All systems</Link>
      <Head title={`${d.system_name}: compliance`}
        meta={[<Link to={`/reports/${d.system_id}/${d.date}`}>Assessment of {d.date}</Link>, d.status === "draft" ? "Based on a draft assessment" : "Based on a final assessment"]}
        lede={LEDE} />
      {HOW}
      <div className="filters hide-desktop" role="group" aria-label="Framework" style={{ marginBottom: 20 }}>
        {d.frameworks.map((f) => <button key={f.source.id} aria-pressed={f.source.id === fw.source.id} onClick={() => setCur(f.source.id)}>{f.source.title.replace(/^OWASP Top 10 for (.+?)( Applications)?$/, "OWASP $1").replace(/ - .*/, "")}</button>)}
      </div>
      <Framework key={fw.source.id} fw={fw} threats={threats} sid={d.system_id} date={d.date} />
    </Shell>
  );
}
