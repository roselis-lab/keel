import { useState } from "react";
import { Link, Navigate, useParams } from "react-router";
import { MITIGATIONS, THREATS, useApi } from "../lib/api";
import type { Finding, Mitigation, Report as R, SystemRow, Threat } from "../lib/types";
import { assessorName, findingTitle, prepare, type Fix, type Prepared } from "../lib/report";
import { cap, clip, firstSentence, harmLabel, plural, STATUS, WHO } from "../lib/text";
import { Grade, Head, Loading, Problem, Shape, Shell } from "../components/ui";
import { ShareButton } from "../components/Share";

type Lib = { threats: Record<string, Threat>; mits: Record<string, Mitigation> };
export const byId = <T extends { id: string }>(xs: T[]) => Object.fromEntries(xs.map((x) => [x.id, x]));

/** /reports/:system — opens the latest report of that system. */
export function LatestReport() {
  const { system } = useParams();
  const s = useApi<[{ series: { date: string }[] }]>(`/reports/${system}`);
  if (s.loading) return <Shell title="Report"><Loading /></Shell>;
  if (s.error) return <Shell title="Report"><Problem error={s.error} what="report" /></Shell>;
  const d = s.data[0].series[0]?.date;
  return d ? <Navigate replace to={`/reports/${system}/${d}`} /> : <Shell title="Report"><div className="empty"><b>No report for this system yet</b>Run an assessment and it appears here.</div></Shell>;
}

export function ReportPage() {
  const { system, date } = useParams();
  const q = useApi<[R, { threats: Threat[] }, { mitigations: Mitigation[] }, { reports: SystemRow[] }]>(`/reports/${system}/${date}`, THREATS, MITIGATIONS, "/reports");
  if (q.loading) return <Shell title="Report"><Loading /></Shell>;
  if (q.error) return <Shell title="Report"><Problem error={q.error} what="report" /></Shell>;
  const [r, t, m, systems] = q.data;
  const lib = { threats: byId(t.threats), mits: byId(m.mitigations) };
  return <ReportView r={r} lib={lib} systems={systems.reports} />;
}

function FixRow({ x, r, lib, n }: { x: Fix; r: R; lib: Lib; n?: number }) {
  const c = lib.mits[x.id || ""];
  const specific = x.reqs.find((q) => q.invariant || q.enforce_at || q.done_check);
  const box = x.status === "already_covered" ? "ok" : x.status === "partial" ? "part" : "";
  return (
    <li>
      <details>
        <summary>
          <span className={`box ${box}`} aria-label={STATUS[x.status]} />
          <span className="ttl">{n ? `${n}. ` : ""}{x.title}</span>
          <span className="closes">{plural(x.risks.length, "risk")} {x.risks.map((f) => <Shape key={f.id} v={f.risk.severity} title={findingTitle(f, lib.threats)} />)}</span>
          <span className="why">{STATUS[x.status]}{x.id ? " · a library control" : " · written for this system"}</span>
        </summary>
        <div className="body">
          {x.text ? <p>{x.text}</p> : c?.purpose && <p>{firstSentence(c.purpose)}</p>}
          {specific && <dl className="kv" style={{ margin: "10px 0" }}>
            {specific.invariant && <><dt>Must always hold</dt><dd>{specific.invariant}</dd></>}
            {specific.enforce_at && <><dt>Enforce at</dt><dd>{specific.enforce_at}</dd></>}
            {specific.done_check && <><dt>Done when</dt><dd>{specific.done_check}</dd></>}
          </dl>}
          {x.reqs.map((q) => q.coverage_note).filter(Boolean).map((t, i) => <p key={i}>{t}</p>)}
          <p>Closes: {x.risks.map((f, i) => <span key={f.id}>{i ? "; " : ""}<Link to={`/reports/${r.system_id}/${r.date}/${f.id}`}>{clip(findingTitle(f, lib.threats), 80)}</Link></span>)}</p>
          {x.id && <p><Link to={`/controls/${x.id}`}>How this control works and how to check it →</Link></p>}
        </div>
      </details>
    </li>
  );
}

function RiskRow({ f, r, P, lib }: { f: Finding; r: R; P: Prepared; lib: Lib }) {
  const [open, setOpen] = useState(false);
  const fixes = P.fixes.filter((x) => x.risks.includes(f));
  return (
    <article className={`risk ${open ? "open" : ""}`} id={f.id}>
      <button className="rhead" aria-expanded={open} onClick={() => setOpen(!open)}>
        <div className="rsev"><Grade f={f} /></div>
        <div className="rt">{findingTitle(f, lib.threats)}</div>
        <div className="rs">{open ? f.scenario : firstSentence(f.scenario)}</div>
        <div className="rside hide-s"><span>{harmLabel(f.harm)}</span></div>
      </button>
      <div className="rbody">
        <dl className="facts">
          <dt>Who could do it</dt><dd>{WHO[f.source.who] || cap(f.source.who)}: {f.source.motive}</dd>
          <dt>What lets it happen</dt><dd>{f.vulnerability}</dd>
          <dt>Fixed by</dt><dd><ul className="plain">{fixes.map((x) => <li key={x.key}>{x.id ? <Link to={`/controls/${x.id}`}>{x.title}</Link> : x.title} <span className="t2 small">· {STATUS[x.status]}</span></li>)}</ul></dd>
        </dl>
        <p><Link className="rlink" to={`/reports/${r.system_id}/${r.date}/${f.id}`}>Open the finding →</Link> <span className="t3 small">its own page, to hand to the developer</span></p>
      </div>
    </article>
  );
}

function Fold({ id, title, count, sub, children }: { id: string; title: string; count?: number; sub: string; children: React.ReactNode }) {
  return (
    <details className="det" id={id} style={{ scrollMarginTop: 72 }}>
      <summary>{title}{count !== undefined ? ` · ${count}` : ""} <span className="t2" style={{ fontWeight: 400 }}>— {sub}</span></summary>
      <div style={{ paddingBottom: 18 }}>{children}</div>
    </details>
  );
}

export function ReportView({ r, lib, systems }: { r: R; lib: Lib; systems: SystemRow[] }) {
  const P = prepare(r, lib.mits);
  const hi = P.count("high");
  const oq = (r.open_questions || []).filter((q) => !q.answer);
  const rest = P.open.length - P.first.length;
  const lede = hi
    ? <p className="lede"><b>{plural(P.findings.length, "risk")} in {r.system_name}, {hi} of them high.</b> {plural(P.first.length, "fix", "fixes")} close all {hi} high risks; {P.open.length} in all.</p>
    : <p className="lede"><b>{plural(P.findings.length, "risk")} in {r.system_name}, none of them high.</b> {plural(P.open.length, "fix", "fixes")} would close them.</p>;
  const toc: [string, string][] = [
    ...(oq.length ? [["questions", `Open questions · ${oq.length}`] as [string, string]] : []),
    ...(P.first.length ? [["first", "Fix these first"] as [string, string]] : []),
    ["risks", `Risks · ${P.findings.length}`], ["fixes", `All fixes · ${P.open.length}`], ["detail", "How this was assessed"],
  ];
  const rail = <><h2>Systems</h2>{systems.map((s) => (
    <Link key={s.system_id} className="item" to={`/reports/${s.system_id}`} aria-current={s.system_id === r.system_id ? "page" : undefined}>
      <b>{s.system_name}</b><span className="num">{s.latest_date} · {s.status}</span>
    </Link>))}</>;
  const side = <nav className="toc" aria-label="On this page">{toc.map(([h, l]) => <a key={h} href={`#${h}`}>{l}</a>)}</nav>;
  const sf = r.surfaces || [];
  return (
    <Shell title={r.system_name} rail={rail} side={side}>
      <Link className="back-s" to="/reports">← All systems</Link>
      <Head title={r.system_name}
        meta={[<span className={`status ${r.status}`}>{cap(r.status)}</span>, <span className="num">Assessed {r.date}</span>, `by ${assessorName(r.assessor)}`,
          P.minutes ? <span className="num">{P.minutes} min run</span> : null, r.delta_summary ? "Re-assessment" : "First assessment"]}
        lede={lede}
        actions={<><ShareButton r={r} fixes={P.open.length} /><Link className="btn" to={`/compliance/${r.system_id}`} data-no-export>Compliance</Link></>} />

      {oq.length > 0 && <div className="qbox" id="questions">
        <h2>{plural(oq.length, "question")} before this report is final</h2>
        <p className="t2">Parts of the report wait on these facts. Each says how to check it.</p>
        <ul>{oq.map((q) => <li key={q.id}><b>{q.question}</b>
          <dl className="kv" style={{ marginTop: 6 }}><dt>How to check</dt><dd>{q.how_to_check}</dd><dt>What it decides</dt><dd>{q.needed_for}</dd><dt>Already looked in</dt><dd className="t2">{q.looked_in}</dd></dl></li>)}</ul>
      </div>}

      {P.first.length > 0 && <div className="first" id="first">
        <h2>Fix these first</h2>
        <p>These {P.first.length} close every high risk. Open one for what it asks and how to tell it is done.</p>
        <ol className="fixes">{P.first.map((x, i) => <FixRow key={x.key} x={x} r={r} lib={lib} n={i + 1} />)}</ol>
        {rest > 0 && <p className="more">Then {plural(rest, "more fix", "more fixes")} for the medium and low risks, in <a href="#fixes">All fixes</a>.</p>}
      </div>}

      <section id="risks"><h2>Risks</h2><p className="sub">Worst first. Each has its own page to hand to the developer.</p>
        {P.findings.map((f) => <RiskRow key={f.id} f={f} r={r} P={P} lib={lib} />)}</section>

      <section id="fixes"><h2>All fixes</h2><p className="sub">Each fix once, with the risks it closes. In the export, each one is a ticket.</p>
        <ul className="fixes">{P.fixes.map((x) => <FixRow key={x.key} x={x} r={r} lib={lib} />)}</ul></section>

      <section id="detail"><h2>How this was assessed</h2><p className="sub">What was ruled out, what the assessment walked, and what it rests on.</p>
        {(r.paused || []).length > 0 && <Fold id="paused" title="Waiting on an answer" count={r.paused!.length} sub="neither a risk nor ruled out yet">
          <ul className="ruled">{r.paused!.map((p) => <li key={p.id}><b>{lib.threats[p.id]?.title || cap(p.id.replace(/^T-/, "").toLowerCase().replace(/-/g, " "))}</b><span className="t2">{p.note}</span></li>)}</ul></Fold>}
        <Fold id="ruled" title="Ruled out" count={r.discarded.length} sub="checked and found not to apply, with the fact that settles it">
          <ul className="ruled">{r.discarded.map((d) => <li key={d.id}><span><Link className="rlink" to={`/threats/${d.id}`}>{lib.threats[d.id]?.title || d.id}</Link><br /><span className="t3 small">{d.by === "review" ? "broken in review" : "the condition holds here"}</span></span><span className="t2">{d.reason}</span></li>)}</ul></Fold>
        {sf.length > 0 && <Fold id="surfaces" title="Where things reach it" count={sf.length} sub="every way in, tool and data path the assessment walked">
          <table className="tbl"><thead><tr><th>What</th><th style={{ width: 100 }}>Kind</th><th>Leads to</th></tr></thead><tbody>
            {sf.map((x) => <tr key={x.id}><td>{x.name}<div className="where">{x.where}</div></td><td data-l="Kind">{{ entry: "Way in", tool: "Tool", data: "Data path", file: "File" }[x.kind]}</td>
              <td data-l="Leads to">{x.outcome.length ? x.outcome.map((o, i) => { const f = P.findings.find((y) => y.id === o); return <span key={o}>{i ? "; " : ""}{f ? <Link to={`/reports/${r.system_id}/${r.date}/${o}`}>{clip(findingTitle(f, lib.threats), 60)}</Link> : <span className="t2">{lib.threats[o]?.title ? clip(lib.threats[o].title, 60) : o}</span>}</span>; }) : <span className="t2">{x.note}</span>}</td></tr>)}
          </tbody></table></Fold>}
        <Fold id="ran" title="Questions asked" count={r.meta.questions.length} sub={`what the assessor asked the system's owner${r.meta.volunteered.length ? `, and ${plural(r.meta.volunteered.length, "fact")} added unprompted` : ""}`}>
          <ul className="qa">{r.meta.questions.map((q, i) => <li key={i}><q>{q.question}</q><div>{q.answer}</div><div className="imp">{q.impact}</div></li>)}
            {r.meta.volunteered.map((v, i) => <li key={"v" + i}><q>Added unprompted</q><div>{v}</div></li>)}</ul></Fold>
        {(r.evidence || []).length > 0 && <Fold id="evidence" title="Evidence" count={r.evidence!.length} sub="every checked claim, pinned to a commit">
          {r.evidence!.map((e) => <div key={e.id} id={`ev-${e.id}`} style={{ marginBottom: 14, maxWidth: "80ch" }}><div className="where"><b>[{e.id}]</b> {e.kind === "read" ? `${e.path}:${e.lines} @ ${e.commit}` : `${e.kind}: ${e.command}`}</div><div className="quote">{e.quote}</div></div>)}</Fold>}
        <p className="t3 small" style={{ marginTop: 14 }}>{P.findings.filter((f) => !f.review && !(f.evidence || []).length).length} of {P.findings.length} grades are unchecked: no evidence attached and nobody else tried to refute them. Each finding's page says which.</p>
      </section>
    </Shell>
  );
}
