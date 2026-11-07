import { Link, useNavigate, useParams } from "react-router";
import { MITIGATIONS, THREATS, useApi } from "../lib/api";
import type { CoverageSource, Mitigation, Report, SystemRow, Threat } from "../lib/types";
import { KIND, KINDS, cap, clip, firstSentence, plural } from "../lib/text";
import { findingTitle, prepare } from "../lib/report";
import { Head, Legend, Loading, Problem, Sev, Shell, Stack, Toggle } from "../components/ui";
import { byId } from "./Report";
import { useState } from "react";

function useEstate() {
  const s = useApi<[{ reports: SystemRow[] }, { threats: Threat[] }, { mitigations: Mitigation[] }]>("/reports", THREATS, MITIGATIONS);
  const r = useApi<Report[]>(...(s.data ? s.data[0].reports.map((x) => `/reports/${x.system_id}/${x.latest_date}`) : [null]));
  if (s.error || r.error) return { error: (s.error || r.error)! };
  if (!s.data || !r.data) return { loading: true as const };
  const threats = byId(s.data[1].threats), mits = byId(s.data[2].mitigations);
  const reps = (r.data as Report[]).filter(Boolean).map((rep) => ({ r: rep, P: prepare(rep, mits) }))
    .sort((a, b) => b.P.count("high") - a.P.count("high") || b.P.findings.length - a.P.findings.length);
  return { reps, threats, mits };
}

const Marks = ({ P }: { P: ReturnType<typeof prepare> }) => <span className="marks">{(["high", "medium", "low"] as const).map((k) => P.count(k) ? <Sev key={k} v={k}>{P.count(k)} {k}</Sev> : null)}</span>;

export function OverviewPage() {
  const e = useEstate();
  const nav = useNavigate();
  if ("error" in e && e.error) return <Shell title="Overview"><Problem error={e.error} what="the overview" /></Shell>;
  if (!("reps" in e) || !e.reps) return <Shell title="Overview"><Loading /></Shell>;
  const { reps, threats, mits } = e;
  if (!reps.length) return <Shell title="Overview"><Head title="Overview" /><div className="empty"><b>No systems assessed yet</b>Run an assessment with the Keel skill and its report shows up here.</div></Shell>;
  const hi = reps.reduce((a, { P }) => a + P.count("high"), 0);
  const open = reps.reduce((a, { P }) => a + P.open.length, 0);
  const recur: Record<string, { r: Report; title: string }[]> = {};
  reps.forEach(({ r, P }) => P.findings.forEach((f) => (recur[f.id] ||= []).push({ r, title: findingTitle(f, threats) })));
  const asks: Record<string, { n: number; systems: string[] }> = {};
  reps.forEach(({ r, P }) => P.open.forEach((x) => { if (!x.id) return; const a = (asks[x.id] ||= { n: 0, systems: [] }); a.n += x.risks.length; a.systems.push(r.system_name); }));
  return (
    <Shell title="Overview">
      <Head title="Overview" lede={<p className="lede"><b>{plural(hi, "high risk")} across {plural(reps.length, "system")}.</b> {plural(open, "fix", "fixes")} asked for and not built.</p>} />
      <section><h2>Systems</h2>
        <table className="tbl"><thead><tr><th>System</th><th>Risks</th><th className="n" style={{ width: 130 }}>Fix first</th><th className="n" style={{ width: 130 }}>Not built</th><th style={{ width: 120 }}>Assessed</th></tr></thead><tbody>
          {reps.map(({ r, P }) => <tr key={r.system_id} className="rowlink" onClick={() => nav(`/reports/${r.system_id}/${r.date}`)}>
            <td><Link className="rlink" to={`/reports/${r.system_id}/${r.date}`} onClick={(ev) => ev.stopPropagation()}>{r.system_name}</Link><div className="t2 small">{clip(firstSentence(r.system_description), 110)}</div></td>
            <td data-l="Risks"><Marks P={P} /></td>
            <td className="n" data-l="Fix first">{P.first.length || "—"}</td>
            <td className="n" data-l="Not built">{P.open.length}</td>
            <td className="num" data-l="Assessed">{r.date}<div className="t3 small">{cap(r.status)}</div></td>
          </tr>)}
        </tbody></table></section>
      <div className="cols2">
        <section style={{ margin: 0 }}><h2>Found in more than one system</h2>
          {!Object.values(recur).some((xs) => xs.length > 1) && <p className="t2">Nothing yet. Each risk so far was found in one system only.</p>}
          <table className="tbl"><tbody>
          {Object.entries(recur).filter(([, xs]) => xs.length > 1).sort((a, b) => b[1].length - a[1].length).slice(0, 5).map(([id, xs]) =>
            <tr key={id}><td>{threats[id] ? <Link className="rlink" to={`/threats/${id}`}>{clip(xs[0].title, 90)}</Link> : clip(xs[0].title, 90)}</td><td className="n" style={{ width: 100 }}>{plural(xs.length, "system")}</td></tr>)}
        </tbody></table></section>
        <section style={{ margin: 0 }}><h2>Asked for most</h2><table className="tbl"><tbody>
          {Object.entries(asks).sort((a, b) => b[1].n - a[1].n).slice(0, 5).map(([id, a]) =>
            <tr key={id}><td><Link className="rlink" to={`/controls/${id}`}>{mits[id]?.name || id}</Link><div className="t3 small">{[...new Set(a.systems)].join(", ")}</div></td><td className="n" style={{ width: 100 }}>{plural(a.n, "risk")}</td></tr>)}
        </tbody></table></section>
      </div>
      <p className="t3 small" style={{ marginTop: 32 }}>Library upkeep lives in the <a href="/edit/overview">library editor</a>.</p>
    </Shell>
  );
}

export function ReportsPage() {
  const e = useEstate();
  const nav = useNavigate();
  if ("error" in e && e.error) return <Shell title="Reports"><Problem error={e.error} what="reports" /></Shell>;
  if (!("reps" in e) || !e.reps) return <Shell title="Reports"><Loading /></Shell>;
  return (
    <Shell title="Reports">
      <Head title="Reports" lede={<p className="lede quiet">One report per assessed system: the risks found, what to fix first, and what was ruled out. Open one to read it or share it with the team that owns the system.</p>}
        actions={<a className="btn" href="/edit/reports">Start a report in the editor</a>} />
      {e.reps.length === 0 ? <div className="empty"><b>No reports yet</b>Run an assessment with the Keel skill and its report shows up here.</div> :
        <table className="tbl"><thead><tr><th>System</th><th>Risks</th><th className="n" style={{ width: 130 }}>Fix first</th><th style={{ width: 140 }}>Latest report</th></tr></thead><tbody>
          {e.reps.map(({ r, P }) => <tr key={r.system_id} className="rowlink" onClick={() => nav(`/reports/${r.system_id}/${r.date}`)}>
            <td><Link className="rlink" to={`/reports/${r.system_id}/${r.date}`} onClick={(ev) => ev.stopPropagation()}>{r.system_name}</Link><div className="t2 small">{clip(firstSentence(r.system_description), 140)}</div></td>
            <td data-l="Risks"><Marks P={P} /></td>
            <td className="n" data-l="Fix first">{P.first.length ? plural(P.first.length, "fix", "fixes") : "—"}</td>
            <td className="num" data-l="Latest report">{r.date}<div className="t3 small">{cap(r.status)}{r.delta_summary ? " · re-assessment" : ""}</div></td>
          </tr>)}
        </tbody></table>}
    </Shell>
  );
}

const COV: Record<string, string> = { covered: "Covered", out_of_scope: "Out of scope", gap: "Gap" };
export function CoveragePage() {
  const { source } = useParams();
  const q = useApi<[{ sources: CoverageSource[] }, { threats: Threat[] }, { mitigations: Mitigation[] }]>("/coverage", THREATS, MITIGATIONS);
  const [view, setView] = useState<"state" | "group">("state");
  if (q.loading) return <Shell title="Coverage"><Loading /></Shell>;
  if (q.error) return <Shell title="Coverage"><Problem error={q.error} what="coverage" /></Shell>;
  const [{ sources }, t, m] = q.data;
  const threats = byId(t.threats), mits = byId(m.mitigations);
  const cs = sources.find((x) => x.source.id === source) || sources[0];
  if (!cs) return <Shell title="Coverage"><Head title="Coverage" /><div className="empty"><b>No frameworks tracked</b>Add a coverage file under catalog/coverage to compare the library with a framework.</div></Shell>;
  const c = cs.counts, n = cs.entries.length;
  const rank = ["gap", "covered", "out_of_scope"];
  const rows = view === "state" ? [...cs.entries].sort((a, b) => rank.indexOf(a.state) - rank.indexOf(b.state)) : [...cs.entries].sort((a, b) => String(a.group).localeCompare(String(b.group)));
  let lastG: string | null | undefined = undefined;
  const p = (x: CoverageSource["counts"]) => [["covered", x.covered], ["out_of_scope", x.out_of_scope], ["gap", x.gap]] as [string, number][];
  const rail = <>{KINDS.map((k, i) => { const xs = sources.filter((x) => x.source.kind === k); return <div key={k} style={{ marginTop: i ? 22 : 0 }}><h2>{KIND[k].many}</h2>
    {xs.length === 0 && <p className="t3 small" style={{ padding: "4px 0" }}>None tracked yet.</p>}
    {xs.map((x) => <Link key={x.source.id} className="item" to={`/coverage/${x.source.id}`} aria-current={x.source.id === cs.source.id ? "page" : undefined}>
    <b>{x.source.title}</b><span>{x.counts.covered} covered · {plural(x.counts.gap, "gap")}</span><Stack parts={p(x.counts)} total={x.entries.length} label={`${x.counts.covered} covered, ${x.counts.gap} gaps`} /></Link>)}</div>; })}</>;
  return (
    <Shell title={`${cs.source.title} coverage`} rail={rail}>
      <Head title={cs.source.title} meta={[KIND[cs.source.kind]?.one, cs.source.version, <span className="num">checked {cs.source.checked}</span>, cs.source.url ? <a href={cs.source.url} target="_blank" rel="noopener noreferrer">the framework</a> : null]}
        lede={<><p className="lede"><b>The library covers {c.covered} of {n} entries.</b> {c.out_of_scope} are out of scope for a deployed system, {plural(c.gap, "gap")}.</p>
          <Stack big parts={p(c)} total={n} label={`${c.covered} covered, ${c.out_of_scope} out of scope, ${c.gap} gaps`} />
          <Legend items={[["covered", "Covered", c.covered], ["out_of_scope", "Out of scope", c.out_of_scope], ["gap", "Gap", c.gap]]} />
          <p className="t2 small" style={{ maxWidth: "72ch" }}>This page measures the library: what Keel can assess against this {cs.source.kind === "best_practice" ? "framework" : KIND[cs.source.kind]?.one.toLowerCase()}. How each assessed system stands against it is on <Link to="/compliance">Compliance</Link>.</p></>} />
      <Toggle label="Order" value={view} onChange={setView} options={[["state", "Gaps first"], ["group", "By group"]]} />
      <table className="tbl"><thead><tr><th style={{ width: 100 }}>Entry</th><th>Name</th><th style={{ width: 130 }}>State</th><th>Covered by</th></tr></thead><tbody>
        {rows.flatMap((e) => {
          const out = [];
          if (view === "group" && e.group !== lastG) { lastG = e.group; out.push(<tr key={"g" + e.group}><td colSpan={4} style={{ paddingTop: 18, fontWeight: 700, borderBottom: "1px solid var(--ink)" }}>{e.group || "Other"}</td></tr>); }
          out.push(<tr key={e.ref}>
            <td><span className="id">{e.ref}</span></td>
            <td><b style={{ fontWeight: 600 }}>{e.title}</b>{e.note && <div className="t2 small" style={{ marginTop: 2 }}>{e.note}</div>}</td>
            <td data-l="State"><span className={`st ${e.state}`}><i className={`k-${e.state}`} />{COV[e.state]}</span></td>
            <td data-l="Covered by" className="small">{[...(e.threats || []).map((x) => <Link key={x} to={`/threats/${x}`}>{clip(threats[x]?.title || x, 60)}</Link>), ...(e.mitigations || []).map((x) => <Link key={x} to={`/controls/${x}`}>{mits[x]?.name || x}</Link>)]
              .reduce<React.ReactNode[]>((a, el, i) => (i ? [...a, "; ", el] : [el]), []) }{!(e.threats || []).length && !(e.mitigations || []).length && <span className="t3">—</span>}</td>
          </tr>);
          return out;
        })}
      </tbody></table>
    </Shell>
  );
}
