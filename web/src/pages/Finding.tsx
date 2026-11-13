import { useState } from "react";
import { Link, useParams } from "react-router";
import { MITIGATIONS, THREATS, useApi } from "../lib/api";
import type { Mitigation, Report, Threat } from "../lib/types";
import { findingTitle, prepare, reqKey } from "../lib/report";
import { cap, firstSentence, harmLabel, STATUS, SURF, WHO } from "../lib/text";
import { Backing, Grade, Head, Loading, Problem, Sev, Shell } from "../components/ui";
import { byId } from "./Report";
import { EvidenceRefs, Ev } from "../components/Evidence";

const ORIGIN = { new: "New with this integration", changed: "Changed by this integration", legacy: "Existed before, unchanged" };

export function FindingPage() {
  const { system, date, finding } = useParams();
  const q = useApi<[Report, { threats: Threat[] }, { mitigations: Mitigation[] }]>(`/reports/${system}/${date}`, THREATS, MITIGATIONS);
  const [full, setFull] = useState(false);
  if (q.loading) return <Shell title="Finding"><Loading /></Shell>;
  if (q.error) return <Shell title="Finding"><Problem error={q.error} what="finding" /></Shell>;
  const [r, t, m] = q.data;
  const threats = byId(t.threats), mits = byId(m.mitigations);
  const P = prepare(r, mits);
  const f = P.findings.find((x) => x.id === finding);
  if (!f) return <Shell title="Finding"><Problem error={Object.assign(new Error("not found"), { status: 404 })} what="finding" /></Shell>;
  const n = P.findings.indexOf(f) + 1;
  const title = findingTitle(f, threats);
  const cutAt = f.requirements.find((q) => q.enforce_at)?.enforce_at;
  const evs = (f.evidence || []).map((id) => (r.evidence || []).find((e) => e.id === id)).filter(Boolean);
  const rail = <><h2>{r.system_name} · risks</h2>{P.findings.map((x) => (
    <Link key={x.id} className="item" to={`/reports/${r.system_id}/${r.date}/${x.id}`} aria-current={x.id === f.id ? "page" : undefined}>
      <b><Sev v={x.risk.severity}>{""}</Sev> {findingTitle(x, threats).slice(0, 72)}{findingTitle(x, threats).length > 72 ? "…" : ""}</b>
    </Link>))}</>;
  const side = <aside className="factcol"><h2>Facts</h2><dl>
    <dt>Way in</dt><dd>{SURF[f.attack_surface || ""] || f.attack_surface || "No channel crossed"}</dd>
    <dt>Exploitation</dt><dd>{f.exploitation_complexity} complexity</dd>
    <dt>Deployment</dt><dd>{f.deployment || "live"}</dd>
    {f.origin && <><dt>Origin</dt><dd>{ORIGIN[f.origin]}</dd></>}
    {f.root_cause && <><dt>Fingerprint</dt><dd className="where">{f.root_cause}</dd></>}
    <dt>Library</dt><dd>{f.from_catalog ? <Link to={`/threats/${f.id}`}>{f.id}</Link> : "not in the library"}</dd>
  </dl></aside>;
  return (
    <EvidenceRefs report={r}>
    <Shell title={title} rail={rail} side={side}>
      <Link className="back-s" to={`/reports/${r.system_id}/${r.date}`}>← {r.system_name} report</Link>
      <Head title={title}
        meta={[<Link to={`/reports/${r.system_id}/${r.date}`}>{r.system_name}</Link>, <span className="num">{r.date}</span>, `Risk ${n} of ${P.findings.length}`, harmLabel(f.harm)]}
        lede={<p className="lede" style={{ maxWidth: "62ch" }}><Ev text={firstSentence(f.scenario)} /></p>} />

      <div className="grade">
        <div><small>Severity{f.risk_today ? ", as designed" : ""}</small><span className={`label ${f.risk.severity}`}>{f.risk.severity}</span></div>
        <div><small>Likelihood{f.risk_today ? ", as designed" : ""}</small><span className="lik" style={{ fontSize: 15, fontWeight: 600, color: "var(--ink)" }}>{cap(f.risk.likelihood)}</span></div>
        {f.risk_today && <div><small>Today, {f.deployment}</small><Grade f={{ risk: f.risk_today }} /></div>}
        <div><small>Evidence</small><Backing f={f} /></div>
      </div>

      <section style={{ marginTop: 28 }}><h2>How it happens</h2>
        <figure aria-label="How the harm happens">
          <div className={`chain ${full ? "open" : ""}`}>
            <div className="link"><small>Who could do it</small><b>{WHO[f.source.who] || cap(f.source.who)}</b><p><Ev text={f.source.motive} /></p></div>
            <div className="link"><small>How they get in</small><b>{SURF[f.attack_surface || ""] || f.attack_surface || "No channel crossed"}</b><p><Ev text={f.source.access} /></p></div>
            <div className="link"><small>What lets it happen</small><b><Ev text={firstSentence(f.vulnerability)} /></b><p><Ev text={f.vulnerability.slice(firstSentence(f.vulnerability).length)} /></p></div>
            <div className="link harm"><small>What gets hurt</small><b>{harmLabel(f.harm)}</b><p><Ev text={f.asset} /></p></div>
          </div>
          {cutAt && <div className="fixrow"><div className="cut"><b>The fix cuts here</b><Ev text={cutAt} /></div></div>}
          <button className="linkbtn" onClick={() => setFull(!full)}>{full ? "Shorten each step" : "Show the full text of each step"}</button>
        </figure>
        <details className="det" style={{ marginTop: 12 }}><summary>The whole scenario</summary><p className="prose"><Ev text={f.scenario} /></p>
          {f.delta && <><h4>What the integration changed</h4><p className="prose"><Ev text={f.delta} /></p></>}</details>
      </section>

      <section><h2>What to build</h2><p className="sub">Each says where it must hold and how to tell it is done.</p>
        {f.requirements.map((q) => {
          const fix = P.fixes.find((x) => x.key === reqKey(q));
          const c = q.mitigation_id ? mits[q.mitigation_id] : undefined;
          const specific = q.invariant || q.enforce_at || q.done_check;
          return (
            <div className="req" key={reqKey(q)}>
              <header>
                <span className={`box ${q.coverage_status === "already_covered" ? "ok" : q.coverage_status === "partial" ? "part" : ""}`} />
                {c ? <Link to={`/controls/${c.id}`}>{c.name}</Link> : <b><Ev text={fix?.title || q.description} /></b>}
                <span className="t2 small">{STATUS[q.coverage_status]}</span>
              </header>
              {!c && q.description && fix?.title !== q.description && <p className="t2" style={{ fontSize: 14, marginBottom: 6 }}><Ev text={q.description} /></p>}
              {specific ? <dl className="kv">
                <dt>Must always hold</dt><dd><Ev text={q.invariant || "—"} /></dd><dt>Enforce at</dt><dd><Ev text={q.enforce_at || "—"} /></dd><dt>Done when</dt><dd><Ev text={q.done_check || "—"} /></dd></dl>
                : c?.purpose && <p className="t2" style={{ fontSize: 14 }}>{firstSentence(c.purpose)} <span className="t3">No check written for this system yet; the control's page says how to check it in general.</span></p>}
              {q.coverage_note && <p className="t2" style={{ fontSize: 14, marginTop: 6 }}><Ev text={q.coverage_note} /></p>}
            </div>
          );
        })}
      </section>

      <section><h2>Why this grade</h2>
        <p className="prose"><Ev text={f.risk.reasoning} /></p>
        {f.risk_today && <p className="prose t2"><b>Today:</b> <Ev text={f.risk_today.reasoning} /></p>}
        {f.review ? <div className="call"><b>Survived review</b>{f.review.by}, verdict “{f.review.verdict}”. <Ev text={f.review.note} /></div>
          : <div className="call quiet"><b>Nobody has tried to refute this grade</b><span className="t2">A {f.risk.severity} grade is firmer once a review has tried to break the chain.</span></div>}
        {evs.length > 0 && <><h4>Evidence</h4>{evs.map((e) => <div key={e!.id} id={`ev-${e!.id}`} style={{ marginBottom: 14, maxWidth: "80ch" }}><div className="where"><b>[{e!.id}]</b> {e!.kind === "read" ? `${e!.path}:${e!.lines} @ ${e!.commit}` : `${e!.kind}: ${e!.command}`}</div><div className="quote">{e!.quote}</div></div>)}</>}
      </section>

      {(f.ignored_mitigations || []).length > 0 && <section><h2>Considered and not applied</h2>
        <ul className="ruled">{f.ignored_mitigations!.map((x) => <li key={x.mitigation_id}><Link className="rlink" to={`/controls/${x.mitigation_id}`}>{mits[x.mitigation_id]?.name || x.mitigation_id}</Link><span className="t2"><Ev text={x.reason} /></span></li>)}</ul></section>}
    </Shell>
    </EvidenceRefs>
  );
}
