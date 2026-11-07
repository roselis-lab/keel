import { useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router";
import { MITIGATIONS, THREATS, useApi } from "../lib/api";
import type { Mitigation, Report, SystemRow, Threat } from "../lib/types";
import { CLASS, clip, failText, firstSentence, harmLabel, Md, plural, SURF, WHO, cap } from "../lib/text";
import { Grade, Head, Loading, Problem, Shell, Toggle } from "../components/ui";
import { byId } from "./Report";

/** Every latest report, for "found in": which systems carry this threat. */
function useLatestReports() {
  const s = useApi<[{ reports: SystemRow[] }]>("/reports");
  const paths = s.data ? s.data[0].reports.map((x) => `/reports/${x.system_id}/${x.latest_date}`) : [null];
  const r = useApi<Report[]>(...paths);
  return s.data && r.data ? (r.data as Report[]).filter(Boolean) : [];
}
const foundIn = (reports: Report[], id: string) => reports.flatMap((r) => r.findings.filter((f) => f.id === id).map((f) => ({ r, f })));
const editLink = (path: string) => <a className="btn" href={`/edit${path}`}>Edit in the library editor</a>;

export function ThreatsPage() {
  const q = useApi<[{ threats: Threat[] }]>(THREATS);
  const reports = useLatestReports();
  const nav = useNavigate();
  const [harm, setHarm] = useState<string | null>(null);
  const [sort, setSort] = useState<"az" | "found">("az");
  if (q.loading) return <Shell title="Threats"><Loading /></Shell>;
  if (q.error) return <Shell title="Threats"><Problem error={q.error} what="threats" /></Shell>;
  const all = q.data[0].threats;
  const harms = [...new Set(all.map((t) => t.harm))];
  let rows = all.filter((t) => !harm || t.harm === harm);
  if (sort === "found") rows = [...rows].sort((a, b) => foundIn(reports, b.id).length - foundIn(reports, a.id).length || a.id.localeCompare(b.id));
  return (
    <Shell title="Threats">
      <Head title="Threats" meta={[`${all.length} threats every system is checked against`]}
        lede={<p className="lede quiet">Each is one sentence saying what goes wrong. Open one for when it does not apply, the weak spots that let it happen, and what stops it.</p>}
        actions={<a className="btn" href="/edit/threats">Add or edit threats</a>} />
      <div className="filters" role="group" aria-label="Filter by harm">
        <button aria-pressed={!harm} onClick={() => setHarm(null)}>All · {all.length}</button>
        {harms.map((h) => <button key={h} aria-pressed={harm === h} onClick={() => setHarm(h)}>{harmLabel(h)} · {all.filter((t) => t.harm === h).length}</button>)}
      </div>
      <Toggle label="Sort" value={sort} onChange={setSort} options={[["az", "A–Z"], ["found", "Found most"]]} />
      <table className="tbl"><thead><tr><th>Threat</th><th style={{ width: 160 }}>Harm</th><th className="n" style={{ width: 130 }}>Stop · reduce</th><th style={{ width: 200 }}>Found in</th></tr></thead><tbody>
        {rows.map((t) => {
          const g = t.mitigations.filter((m) => m.strength === "gating").length, fi = foundIn(reports, t.id);
          return <tr key={t.id} className="rowlink" onClick={() => nav(`/threats/${t.id}`)}>
            <td><Link className="rlink" to={`/threats/${t.id}`} onClick={(e) => e.stopPropagation()}>{t.title}</Link></td>
            <td data-l="Harm">{harmLabel(t.harm)}</td>
            <td className="n" data-l="Stop · reduce">{g} · {t.mitigations.length - g}</td>
            <td data-l="Found in">{fi.length ? fi.map(({ r }) => r.system_name).join(", ") : <span className="t3">—</span>}</td>
          </tr>;
        })}
      </tbody></table>
    </Shell>
  );
}

export function ThreatPage() {
  const { id } = useParams();
  const q = useApi<[Threat, { threats: Threat[] }, { mitigations: Mitigation[] }]>(`/threats/${id}`, THREATS, MITIGATIONS);
  const reports = useLatestReports();
  if (q.loading) return <Shell title="Threat"><Loading /></Shell>;
  if (q.error) return <Shell title="Threat"><Problem error={q.error} what="threat" /></Shell>;
  const [t, list, ms] = q.data;
  const mits = byId(ms.mitigations);
  const byComp: Record<string, Threat["weaknesses"]> = {};
  t.weaknesses.forEach((w) => (byComp[w.component] ||= []).push(w));
  const gating = t.mitigations.filter((m) => m.strength === "gating"), soft = t.mitigations.filter((m) => m.strength !== "gating");
  const fi = foundIn(reports, t.id);
  const ctl = (m: Threat["mitigations"][number]) => <div className="ctl" key={m.id}>
    <div><Link className="rlink" to={`/controls/${m.id}`}>{mits[m.id]?.name || m.id}</Link><div className="t3 small">{CLASS[mits[m.id]?.mitigation_class] || ""}</div></div><p>{m.rationale}</p></div>;
  const rail = <><h2>Threats</h2>{list.threats.map((x) => <Link key={x.id} className="item" to={`/threats/${x.id}`} aria-current={x.id === t.id ? "page" : undefined}><b style={{ fontWeight: 500 }}>{x.title}</b></Link>)}</>;
  const frameworks = new Set((t.cited_by || []).map((c) => c.source_id)).size;
  return (
    <Shell title={t.title} rail={rail}>
      <Link className="back-s" to="/threats">← All threats</Link>
      <Head title={t.title} meta={[harmLabel(t.harm), t.source.map((s) => WHO[s] || cap(s)).join(", "), plural(frameworks, "framework") + " name it", <span className="id">{t.id}</span>]}
        actions={editLink(`/threats/${t.id}`)} />
      {t.reachability && <div className="call" style={{ marginBottom: 36 }}><b>Does not apply when</b>{t.reachability}</div>}
      {fi.length > 0 && <section><h2>Found in</h2><table className="tbl"><tbody>{fi.map(({ r, f }) =>
        <tr key={r.system_id}><td><Link className="rlink" to={`/reports/${r.system_id}/${r.date}/${t.id}`}>{r.system_name}</Link> <span className="num t2">{r.date}</span></td><td><Grade f={f} /></td></tr>)}</tbody></table></section>}
      <section><h2>What stops it · {gating.length}</h2><p className="sub">Controls that block the path when they hold.</p>{gating.map(ctl)}</section>
      {soft.length > 0 && <section><h2>What reduces or detects it · {soft.length}</h2>{soft.map(ctl)}</section>}
      <section><h2>Weak spots · {t.weaknesses.length}</h2><p className="sub">The conditions in a system that let it happen, by the part they sit in.</p>
        {Object.entries(byComp).map(([c, ws]) => <div key={c}><h4>{cap(c.replace("-", " "))} · {ws.length}</h4>
          {ws.map((w, i) => <div className="wk" key={i}><div className="t3 small">{(w.surface || []).map((s) => SURF[s] || s).join(", ")}{w.nature === "secondary" ? " · secondary" : ""}</div>{w.text}</div>)}</div>)}</section>
      {(t.references || []).length > 0 && <section><h2>Seen in the wild · {t.references!.length}</h2><ul className="qa">{t.references!.map((x) =>
        <li key={x.url}><a href={x.url} target="_blank" rel="noopener noreferrer"><b>{x.title}</b></a><div className="imp">{x.note}</div></li>)}</ul></section>}
      {(t.cited_by || []).length > 0 && <section><h2>Frameworks that name it</h2><table className="tbl"><tbody>{t.cited_by!.map((c, i) =>
        <tr key={i}><td style={{ width: "40%" }}><Link to={`/coverage/${c.source_id}`}>{c.source_title}</Link></td><td><span className="id">{c.ref}</span> {c.title}</td></tr>)}</tbody></table>
        {t.positioning && <details className="det"><summary>How this record sits against them</summary><p className="prose">{t.positioning}</p></details>}</section>}
    </Shell>
  );
}

export function ControlsPage() {
  const q = useApi<[{ mitigations: Mitigation[] }, { threats: Threat[] }]>(MITIGATIONS, THREATS);
  const nav = useNavigate();
  const [kind, setKind] = useState<string | null>(null);
  const closes = useMemo(() => {
    const c: Record<string, number> = {};
    q.data?.[1].threats.forEach((t) => t.mitigations.forEach((m) => (c[m.id] = (c[m.id] || 0) + 1)));
    return c;
  }, [q.data]);
  if (q.loading) return <Shell title="Controls"><Loading /></Shell>;
  if (q.error) return <Shell title="Controls"><Problem error={q.error} what="controls" /></Shell>;
  const all = q.data[0].mitigations;
  const kinds = [...new Set(all.map((m) => m.mitigation_class))];
  const rows = all.filter((m) => !kind || m.mitigation_class === kind);
  return (
    <Shell title="Controls">
      <Head title="Controls" meta={[`${all.length} controls, each with how to tell it works`]}
        lede={<p className="lede quiet">What a system can put in place. Each page says when it applies, where it sits, how it fails and the checks that prove it holds.</p>}
        actions={<a className="btn" href="/edit/mitigations">Add or edit controls</a>} />
      <div className="filters" role="group" aria-label="Filter by kind">
        <button aria-pressed={!kind} onClick={() => setKind(null)}>All · {all.length}</button>
        {kinds.map((k) => <button key={k} aria-pressed={kind === k} onClick={() => setKind(k)}>{CLASS[k] || k} · {all.filter((m) => m.mitigation_class === k).length}</button>)}
      </div>
      <table className="tbl"><thead><tr><th>Control</th><th style={{ width: 130 }}>Kind</th><th className="n" style={{ width: 110 }}>Closes</th><th className="n" style={{ width: 110 }}>Checks</th></tr></thead><tbody>
        {rows.map((m) => <tr key={m.id} className="rowlink" onClick={() => nav(`/controls/${m.id}`)}>
          <td><Link className="rlink" to={`/controls/${m.id}`} onClick={(e) => e.stopPropagation()}>{m.name}</Link>{m.purpose && <div className="t2 small">{clip(firstSentence(m.purpose), 140)}</div>}</td>
          <td data-l="Kind">{CLASS[m.mitigation_class] || m.mitigation_class}</td>
          <td className="n" data-l="Closes">{plural(closes[m.id] || 0, "threat")}</td>
          <td className="n" data-l="Checks">{(m.validation || []).length || <span className="t3">none yet</span>}</td>
        </tr>)}
      </tbody></table>
    </Shell>
  );
}

export function ControlPage() {
  const { id } = useParams();
  const q = useApi<[Mitigation, { threats: Threat[] }]>(`/mitigations/${id}`, THREATS);
  const reports = useLatestReports();
  if (q.loading) return <Shell title="Control"><Loading /></Shell>;
  if (q.error) return <Shell title="Control"><Problem error={q.error} what="control" /></Shell>;
  const [m, t] = q.data;
  const closes = t.threats.flatMap((x) => x.mitigations.filter((l) => l.id === m.id).map((l) => ({ t: x, l })));
  const asked = reports.flatMap((r) => r.findings.flatMap((f) => f.requirements.filter((q) => q.mitigation_id === m.id).map((q) => ({ r, f, q }))));
  return (
    <Shell title={m.name}>
      <Link className="back-s" to="/controls">← All controls</Link>
      <Head title={m.name} meta={[CLASS[m.mitigation_class] || m.mitigation_class, m.failure_behavior ? failText(m.failure_behavior.value) : null, plural(closes.length, "threat") + " it closes", <span className="id">{m.id}</span>]}
        lede={m.purpose && <p className="lede quiet">{m.purpose}</p>} actions={editLink(`/mitigations/${m.id}`)} />
      {m.scope || m.out_of_scope ? <div className="cols2">
        <div className="panel"><h3>Applies when</h3>{m.scope ? <Md text={m.scope} /> : <p className="t3">Not written yet.</p>}</div>
        <div className="panel"><h3>Does not cover</h3>{m.out_of_scope ? <Md text={m.out_of_scope} /> : <p className="t3">Not written yet.</p>}</div>
      </div> : null}
      {(m.validation || []).length > 0 && <section><h2>How to tell it works · {m.validation!.length}</h2><p className="sub">Checks a reviewer can run. The core ones must hold for it to count at all.</p>
        <ul className="checks">{m.validation!.map((v, i) => <li key={i}><span className="box" /><span>{v.base && <b>Core. </b>}{v.criterion}</span></li>)}</ul></section>}
      {(() => {
        const gaps = [!m.scope && "when it applies", !m.out_of_scope && "what it does not cover", !(m.validation || []).length && "the checks that prove it holds"].filter(Boolean) as string[];
        return gaps.length > 0 && <p className="call quiet" style={{ marginBottom: 32 }}><b>Not written yet</b>This card does not yet say {gaps.length > 1 ? gaps.slice(0, -1).join(", ") + " or " + gaps[gaps.length - 1] : gaps[0]}. Add {gaps.length > 1 ? "them" : "it"} in the <a href={`/edit/mitigations/${m.id}`}>library editor</a>.</p>;
      })()}
      {(m.formal_implementation_risk || (m.anti_patterns || []).length > 0) && <section><h2>Looks done, isn't</h2>
        {m.formal_implementation_risk && <div className="call warn"><b>The usual failure</b>{m.formal_implementation_risk}</div>}
        <ul className="qa">{(m.anti_patterns || []).map((a, i) => <li key={i}>{a}</li>)}</ul></section>}
      {m.failure_behavior && <section><h2>When it breaks</h2><p className="prose"><b>{failText(m.failure_behavior.value)}.</b> {m.failure_behavior.note}</p></section>}
      {(m.locus || m.control_mechanism) && <section><h2>Where it sits</h2>{m.locus && <p className="prose">{m.locus.note}</p>}<Md text={m.control_mechanism} /></section>}
      {m.telemetry && <section><h2>What it records</h2><table className="tbl"><thead><tr><th style={{ width: 200 }}>Event</th><th>What it records</th></tr></thead><tbody>
        {m.telemetry.events.map((e) => <tr key={e.name}><td className="where" data-l="Event">{e.name}</td><td>{e.records}<div className="t3 small" style={{ marginTop: 4 }}>{e.attributes.join(" · ")}</div></td></tr>)}</tbody></table>
        <p className="t2" style={{ marginTop: 10, fontSize: 14 }}>{m.telemetry.evidence}</p></section>}
      <section><h2>Closes · {closes.length}</h2><table className="tbl"><tbody>{closes.map(({ t, l }) =>
        <tr key={t.id}><td style={{ width: "45%" }}><Link className="rlink" to={`/threats/${t.id}`}>{t.title}</Link><div className="t3 small">{l.strength === "gating" ? "stops it" : "reduces it"}</div></td><td className="t2" style={{ fontSize: 14 }}>{l.rationale}</td></tr>)}</tbody></table></section>
      {asked.length > 0 && <section><h2>Asked for in assessments</h2><table className="tbl"><tbody>{asked.map(({ r, f, q }, i) =>
        <tr key={i}><td><Link className="rlink" to={`/reports/${r.system_id}/${r.date}/${f.id}`}>{r.system_name}</Link></td><td><Grade f={f} /></td><td>{q.coverage_status === "needs_implementation" ? "Not built" : q.coverage_status === "partial" ? "Partly in place" : "In place"}</td></tr>)}</tbody></table></section>}
      {(m.faq || []).length > 0 && <section><h2>Questions</h2>{m.faq!.map((x, i) => <details className="det" key={i}><summary>{x.question}</summary><p className="prose">{x.answer}</p></details>)}</section>}
    </Shell>
  );
}
