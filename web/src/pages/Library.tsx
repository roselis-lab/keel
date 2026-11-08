import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useLocation, useNavigate, useParams, useSearchParams } from "react-router";
import { MITIGATIONS, THREATS, useApi } from "../lib/api";
import type { Mitigation, Report, SystemRow, Threat } from "../lib/types";
import { CLASS, clip, failText, firstSentence, harmLabel, Md, plural, SURF, WHO, cap } from "../lib/text";
import { Grade, Head, Loading, Problem, Shell } from "../components/ui";
import { byId } from "./Report";

/* The library: threats and controls, linked both ways.
   - A list page is a table with a search box and filters. Both live in the address, so
     coming back from a record lands on the same narrowed list.
   - A record page keeps the list beside it (from 1024px), searchable, with a switch
     between threats and controls, so moving to the next record or across a link is one
     click and the list does not lose its place. j / k step through the list.
   - Every link between a threat and a control says which way it works (stops or
     reduces) and why, on both sides. */

/** Every latest report, for "found in": which systems carry this threat. */
function useLatestReports() {
  const s = useApi<[{ reports: SystemRow[] }]>("/reports");
  const paths = s.data ? s.data[0].reports.map((x) => `/reports/${x.system_id}/${x.latest_date}`) : [null];
  const r = useApi<Report[]>(...paths);
  return s.data && r.data ? (r.data as Report[]).filter(Boolean) : [];
}
const foundIn = (reports: Report[], id: string) => reports.flatMap((r) => r.findings.filter((f) => f.id === id).map((f) => ({ r, f })));

const norm = (s: string) => s.toLowerCase();
const threatText = (t: Threat, names: Record<string, string>) =>
  norm([t.id, t.title, harmLabel(t.harm), t.reachability, ...t.weaknesses.map((w) => w.text), ...t.mitigations.map((m) => names[m.id] || m.id)].join(" "));
const controlText = (m: Mitigation) => norm([m.id, m.name, CLASS[m.mitigation_class], m.purpose].join(" "));
const matches = (hay: string, q: string) => norm(q).split(/\s+/).filter(Boolean).every((w) => hay.includes(w));

/** "/" puts the cursor in the search box from anywhere on the page. */
function useSlashFocus(ref: React.RefObject<HTMLInputElement | null>) {
  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      const t = e.target as HTMLElement;
      if (e.key === "/" && !/INPUT|TEXTAREA|SELECT/.test(t.tagName) && !t.isContentEditable) { e.preventDefault(); ref.current?.focus(); }
    };
    addEventListener("keydown", h);
    return () => removeEventListener("keydown", h);
  }, [ref]);
}

function Search({ value, onChange, label, count, total }: { value: string; onChange: (v: string) => void; label: string; count: number; total: number }) {
  const ref = useRef<HTMLInputElement>(null);
  useSlashFocus(ref);
  return <div className="search">
    <svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="7" cy="7" r="5" fill="none" stroke="currentColor" strokeWidth="1.6" /><path d="m11 11 3.5 3.5" stroke="currentColor" strokeWidth="1.6" /></svg>
    <input ref={ref} type="search" value={value} onChange={(e) => onChange(e.target.value)} placeholder={label} aria-label={label} />
    {value ? <span className="search-n">{count} of {total}</span> : <kbd title="Press / to search">/</kbd>}
  </div>;
}

/** Saved or deleted a moment ago in the editor: say so once, without moving anything. */
function Saved() {
  const s = (useLocation().state as { saved?: boolean | string } | null)?.saved;
  const [on, setOn] = useState(!!s);
  useEffect(() => { if (!s) return; setOn(true); const t = setTimeout(() => setOn(false), 3500); return () => clearTimeout(t); }, [s]);
  return on ? <p className="toast" role="status">{s === "deleted" ? "Deleted from the catalog." : "Saved to the catalog."}</p> : null;
}

/* ---------- the list beside a record ---------- */

function LibRail({ kind, current, threats, controls }: { kind: "threats" | "controls"; current: string; threats: Threat[]; controls: Mitigation[] }) {
  const [tab, setTab] = useState(kind);
  const [q, setQ] = useState("");
  const names = useMemo(() => Object.fromEntries(controls.map((m) => [m.id, m.name])), [controls]);
  const ref = useRef<HTMLElement>(null);
  useEffect(() => setTab(kind), [kind, current]);
  // Keep the open record in view inside the rail, without scrolling the page.
  useEffect(() => {
    const box = ref.current?.parentElement, a = ref.current?.querySelector<HTMLElement>('[aria-current="page"]');
    if (box && a && (a.offsetTop < box.scrollTop || a.offsetTop > box.scrollTop + box.clientHeight - 60)) box.scrollTop = a.offsetTop - 160;
  }, [current, tab]);
  const items = tab === "threats"
    ? threats.filter((t) => !q || matches(threatText(t, names), q)).map((t) => ({ id: t.id, to: `/threats/${t.id}`, title: t.title, meta: harmLabel(t.harm) }))
    : [...controls].sort((a, b) => a.name.localeCompare(b.name)).filter((m) => !q || matches(controlText(m), q)).map((m) => ({ id: m.id, to: `/controls/${m.id}`, title: m.name, meta: CLASS[m.mitigation_class] || m.mitigation_class }));
  const one = tab === "threats" ? "threat" : "control";
  return <nav className="librail" aria-label="Library" ref={ref}>
    <div className="libhead">
      <div className="libtabs" role="tablist">
        <button role="tab" aria-selected={tab === "threats"} onClick={() => setTab("threats")}>Threats <span>{threats.length}</span></button>
        <button role="tab" aria-selected={tab === "controls"} onClick={() => setTab("controls")}>Controls <span>{controls.length}</span></button>
      </div>
      <div className="search sm">
        <input type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder={`Find a ${one}`} aria-label={`Find a ${one}`} />
      </div>
    </div>
    {items.length === 0 && <p className="t3 small" style={{ padding: "8px 12px" }}>Nothing matches.</p>}
    {items.map((x) => <Link key={x.id} className="item" to={x.to} aria-current={x.id === current ? "page" : undefined}><b>{x.title}</b><span>{x.meta}</span></Link>)}
  </nav>;
}

/** Previous and next in the list order; j and k do the same from the keyboard. */
function Step({ ids, current, base, label }: { ids: { id: string; title: string }[]; current: string; base: string; label: string }) {
  const nav = useNavigate();
  const i = ids.findIndex((x) => x.id === current);
  const prev = i > 0 ? ids[i - 1] : null, next = i >= 0 && i < ids.length - 1 ? ids[i + 1] : null;
  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      const t = e.target as HTMLElement;
      if (/INPUT|TEXTAREA|SELECT/.test(t.tagName) || e.metaKey || e.ctrlKey || e.altKey) return;
      if (e.key === "j" && next) nav(`${base}/${next.id}`);
      if (e.key === "k" && prev) nav(`${base}/${prev.id}`);
    };
    addEventListener("keydown", h);
    return () => removeEventListener("keydown", h);
  }, [prev, next, base, nav]);
  if (i < 0) return null;
  return <nav className="step" aria-label={label}>
    {prev ? <Link to={`${base}/${prev.id}`} rel="prev"><small>Previous · k</small>{prev.title}</Link> : <span />}
    {next ? <Link to={`${base}/${next.id}`} rel="next" className="nx"><small>Next · j</small>{next.title}</Link> : <span />}
  </nav>;
}

const Toc = ({ items }: { items: [string, string][] }) =>
  <nav className="toc" aria-label="On this page">{items.map(([h, l]) => <a key={h} href={`#${h}`}>{l}</a>)}</nav>;
const when = (ok: unknown, item: [string, string]): [string, string][] => (ok ? [item] : []);

const EditIcon = () => <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M11.5 2.5 13.5 4.5 5.5 12.5 2.5 13.5 3.5 10.5z" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" /></svg>;
const PlusIcon = () => <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 3v10M3 8h10" stroke="currentColor" strokeWidth="1.8" /></svg>;

/** The list's filter and search, kept in the address. */
function useListParams() {
  const [sp, setSp] = useSearchParams();
  const put = (k: string, v: string | null, also: string[] = []) => { const n = new URLSearchParams(sp); if (v) n.set(k, v); else n.delete(k); also.forEach((x) => n.delete(x)); setSp(n, { replace: true }); };
  const clear = () => setSp({}, { replace: true });
  return { sp, put, clear };
}

/* ---------- threats ---------- */

export function ThreatsPage() {
  const q = useApi<[{ threats: Threat[] }, { mitigations: Mitigation[] }]>(THREATS, MITIGATIONS);
  const reports = useLatestReports();
  const nav = useNavigate();
  const { sp, put, clear } = useListParams();
  const text = sp.get("q") || "", harm = sp.get("harm"), sort = sp.get("sort") === "found" ? "found" : "az";
  if (q.loading) return <Shell title="Threats"><Loading /></Shell>;
  if (q.error) return <Shell title="Threats"><Problem error={q.error} what="threats" /></Shell>;
  const [{ threats: all }, { mitigations }] = q.data;
  const names = Object.fromEntries(mitigations.map((m) => [m.id, m.name]));
  const harms = [...new Set(all.map((t) => t.harm))];
  let rows = all.filter((t) => (!harm || t.harm === harm) && (!text || matches(threatText(t, names), text)));
  if (sort === "found") rows = [...rows].sort((a, b) => foundIn(reports, b.id).length - foundIn(reports, a.id).length || a.id.localeCompare(b.id));
  return (
    <Shell title="Threats">
      <Saved />
      <Head title="Threats" meta={[`${all.length} threats every system is checked against`, <Link key="c" to="/controls">{mitigations.length} controls answer them</Link>]}
        lede={<p className="lede quiet">Each is one sentence saying what goes wrong. Open one for when it does not apply, the weak spots that let it happen, and the controls that stop it.</p>}
        actions={<Link className="btn" to="/threats/new"><PlusIcon />New threat</Link>} />
      <div className="listbar">
        <Search value={text} onChange={(v) => put("q", v || null)} label="Search threats, weak spots, controls" count={rows.length} total={all.length} />
        <div className="toggle" role="group" aria-label="Sort">
          <button aria-pressed={sort === "az"} onClick={() => put("sort", null)}>A–Z</button>
          <button aria-pressed={sort === "found"} onClick={() => put("sort", "found")}>Found most</button>
        </div>
      </div>
      <div className="filters" role="group" aria-label="Filter by harm">
        <button aria-pressed={!harm} onClick={() => put("harm", null)}>All · {all.length}</button>
        {harms.map((h) => <button key={h} aria-pressed={harm === h} onClick={() => put("harm", harm === h ? null : h)}>{harmLabel(h)} · {all.filter((t) => t.harm === h).length}</button>)}
      </div>
      {rows.length === 0 ? <div className="empty"><b>No threats match</b>Nothing matches “{text}”{harm ? ` under ${harmLabel(harm)}` : ""}. <button className="linkbtn" onClick={clear}>Clear search and filters</button></div> :
      <table className="tbl lib"><thead><tr><th>Threat</th><th className="fit">Harm</th><th className="fit n" title="Controls that stop it · controls that reduce it">Stops · reduces</th><th className="fit">Found in</th></tr></thead><tbody>
        {rows.map((t) => {
          const g = t.mitigations.filter((m) => m.strength === "gating").length, s = t.mitigations.length - g, fi = foundIn(reports, t.id);
          return <tr key={t.id} className="rowlink" onClick={() => nav(`/threats/${t.id}`)}>
            <td><Link className="rlink" to={`/threats/${t.id}`} onClick={(e) => e.stopPropagation()}>{t.title}</Link></td>
            <td className="fit m">{harmLabel(t.harm)}</td>
            <td className="fit n m" title={`${g} stop it, ${s} reduce it`}><span className="wide-only">{g} · {s}</span><span className="narrow-only">{g} stop, {s} reduce</span></td>
            <td className={`fit wrap m${fi.length ? "" : " none"}`}>{fi.length ? <><span className="narrow-only">Found in </span>{fi.map(({ r }) => r.system_name).join(", ")}</> : <span className="t3 wide-only">—</span>}</td>
          </tr>;
        })}
      </tbody></table>}
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
    <div><Link className="rlink" to={`/controls/${m.id}`} state={{ from: { to: `/threats/${t.id}`, title: t.title } }}>{mits[m.id]?.name || m.id}</Link><div className="t3 small">{CLASS[mits[m.id]?.mitigation_class] || ""}</div></div><p>{m.rationale}</p></div>;
  const frameworks = new Set((t.cited_by || []).map((c) => c.source_id)).size;
  const toc: [string, string][] = [
    ...when(t.reachability, ["rule-out", "Does not apply when"]),
    ...when(fi.length, ["found", "Found in"]),
    ["stops", `Stops it · ${gating.length}`],
    ...when(soft.length, ["reduces", `Reduces it · ${soft.length}`]),
    ["weak", `Weak spots · ${t.weaknesses.length}`],
    ...when((t.references || []).length, ["wild", "Seen in the wild"]),
    ...when((t.cited_by || []).length, ["frameworks", "Frameworks"]),
  ];
  return (
    <Shell title={t.title} rail={<LibRail kind="threats" current={t.id} threats={list.threats} controls={ms.mitigations} />} side={<Toc items={toc} />}>
      <Saved />
      <nav className="crumbs" aria-label="Breadcrumb"><Link to="/threats">Threats</Link><span>/</span><span className="id" aria-current="page">{t.id}</span></nav>
      <Head title={t.title} meta={[harmLabel(t.harm), t.source.map((s) => WHO[s] || cap(s)).join(", "), plural(frameworks, "framework") + " name it"]}
        actions={<Link className="btn" to={`/threats/${t.id}/edit`}><EditIcon />Edit threat</Link>} />
      {t.reachability && <div className="call" id="rule-out" style={{ marginBottom: 36 }}><b>Does not apply when</b>{t.reachability}</div>}
      {fi.length > 0 && <section id="found"><h2>Found in</h2><table className="tbl"><tbody>{fi.map(({ r, f }) =>
        <tr key={r.system_id}><td><Link className="rlink" to={`/reports/${r.system_id}/${r.date}/${t.id}`}>{r.system_name}</Link> <span className="num t2">{r.date}</span></td><td><Grade f={f} /></td></tr>)}</tbody></table></section>}
      <section id="stops"><h2>What stops it · {gating.length}</h2><p className="sub">Controls that block the path when they hold.</p>
        {gating.length ? gating.map(ctl) : <p className="t2">No control stops it yet. <Link to={`/threats/${t.id}/edit`}>Link one</Link>.</p>}</section>
      {soft.length > 0 && <section id="reduces"><h2>What reduces or detects it · {soft.length}</h2>{soft.map(ctl)}</section>}
      <section id="weak"><h2>Weak spots · {t.weaknesses.length}</h2><p className="sub">The conditions in a system that let it happen, by the part they sit in.</p>
        {Object.entries(byComp).map(([c, ws]) => <div key={c}><h4>{cap(c.replace("-", " "))} · {ws.length}</h4>
          {ws.map((w, i) => <div className="wk" key={i}><div className="t3 small">{(w.surface || []).map((s) => SURF[s] || s).join(", ")}{w.nature === "secondary" ? " · secondary" : ""}</div>{w.text}</div>)}</div>)}</section>
      {(t.references || []).length > 0 && <section id="wild"><h2>Seen in the wild · {t.references!.length}</h2><ul className="qa">{t.references!.map((x) =>
        <li key={x.url}><a href={x.url} target="_blank" rel="noopener noreferrer"><b>{x.title}</b></a><div className="imp">{x.note}</div></li>)}</ul></section>}
      {(t.cited_by || []).length > 0 && <section id="frameworks"><h2>Frameworks that name it</h2><table className="tbl"><tbody>{t.cited_by!.map((c, i) =>
        <tr key={i}><td style={{ width: "40%" }}><Link to={`/coverage/${c.source_id}`}>{c.source_title}</Link></td><td><span className="id">{c.ref}</span> {c.title}</td></tr>)}</tbody></table>
        {t.positioning && <details className="det"><summary>How this record sits against them</summary><p className="prose">{t.positioning}</p></details>}</section>}
      <Step ids={list.threats.map((x) => ({ id: x.id, title: x.title }))} current={t.id} base="/threats" label={`Step through ${list.threats.length} threats`} />
    </Shell>
  );
}

/* ---------- controls ---------- */

export function ControlsPage() {
  const q = useApi<[{ mitigations: Mitigation[] }, { threats: Threat[] }]>(MITIGATIONS, THREATS);
  const nav = useNavigate();
  const { sp, put, clear } = useListParams();
  const text = sp.get("q") || "", kind = sp.get("kind"), gap = sp.get("gap") === "checks";
  const closes = useMemo(() => {
    const c: Record<string, number> = {};
    q.data?.[1].threats.forEach((t) => t.mitigations.forEach((m) => (c[m.id] = (c[m.id] || 0) + 1)));
    return c;
  }, [q.data]);
  if (q.loading) return <Shell title="Controls"><Loading /></Shell>;
  if (q.error) return <Shell title="Controls"><Problem error={q.error} what="controls" /></Shell>;
  const all = [...q.data[0].mitigations].sort((a, b) => a.name.localeCompare(b.name));
  const kinds = [...new Set(all.map((m) => m.mitigation_class))];
  const noChecks = all.filter((m) => !(m.validation || []).length).length;
  const rows = all.filter((m) => (!kind || m.mitigation_class === kind) && (!gap || !(m.validation || []).length) && (!text || matches(controlText(m), text)));
  return (
    <Shell title="Controls">
      <Saved />
      <Head title="Controls" meta={[`${all.length} controls, each with how to tell it works`, <Link key="t" to="/threats">{q.data[1].threats.length} threats they answer</Link>]}
        lede={<p className="lede quiet">What a system can put in place. Each page says which threats it closes, when it applies, how it fails and the checks that prove it holds.</p>}
        actions={<Link className="btn" to="/controls/new"><PlusIcon />New control</Link>} />
      <div className="listbar">
        <Search value={text} onChange={(v) => put("q", v || null)} label="Search controls by name or purpose" count={rows.length} total={all.length} />
      </div>
      <div className="filters" role="group" aria-label="Filter">
        <button aria-pressed={!kind && !gap} onClick={() => put("kind", null, ["gap"])}>All · {all.length}</button>
        {kinds.map((k) => <button key={k} aria-pressed={kind === k} onClick={() => put("kind", kind === k ? null : k)}>{CLASS[k] || k} · {all.filter((m) => m.mitigation_class === k).length}</button>)}
        {noChecks > 0 && <button aria-pressed={gap} onClick={() => put("gap", gap ? null : "checks")}>No checks yet · {noChecks}</button>}
      </div>
      {rows.length === 0 ? <div className="empty"><b>No controls match</b>Try fewer words, or <button className="linkbtn" onClick={clear}>clear search and filters</button>.</div> :
      <table className="tbl lib"><thead><tr><th>Control</th><th className="fit">Kind</th><th className="fit n">Closes</th><th className="fit n">Checks</th></tr></thead><tbody>
        {rows.map((m) => <tr key={m.id} className="rowlink" onClick={() => nav(`/controls/${m.id}`)}>
          <td><Link className="rlink" to={`/controls/${m.id}`} onClick={(e) => e.stopPropagation()}>{m.name}</Link>{m.purpose && <div className="t2 small">{clip(firstSentence(m.purpose), 140)}</div>}</td>
          <td className="fit m">{CLASS[m.mitigation_class] || m.mitigation_class}</td>
          <td className="fit n m">{plural(closes[m.id] || 0, "threat")}</td>
          <td className="fit n m">{(m.validation || []).length ? plural(m.validation!.length, "check") : <span className="t3">no checks yet</span>}</td>
        </tr>)}
      </tbody></table>}
    </Shell>
  );
}

export function ControlPage() {
  const { id } = useParams();
  const q = useApi<[Mitigation, { threats: Threat[] }, { mitigations: Mitigation[] }]>(`/mitigations/${id}`, THREATS, MITIGATIONS);
  const reports = useLatestReports();
  const from = (useLocation().state as { from?: { to: string; title: string } } | null)?.from;
  if (q.loading) return <Shell title="Control"><Loading /></Shell>;
  if (q.error) return <Shell title="Control"><Problem error={q.error} what="control" /></Shell>;
  const [m, t, all] = q.data;
  const closes = t.threats.flatMap((x) => x.mitigations.filter((l) => l.id === m.id).map((l) => ({ t: x, l })));
  const asked = reports.flatMap((r) => r.findings.flatMap((f) => f.requirements.filter((q) => q.mitigation_id === m.id).map((q) => ({ r, f, q }))));
  const sorted = [...all.mitigations].sort((a, b) => a.name.localeCompare(b.name));
  const names = byId(all.mitigations);
  const requires = m.requires || [];
  const gaps = [!m.scope && "when it applies", !m.out_of_scope && "what it does not cover", !(m.validation || []).length && "the checks that prove it holds"].filter(Boolean) as string[];
  const toc: [string, string][] = [
    ["closes", `Closes · ${closes.length}`],
    ...when(m.scope || m.out_of_scope, ["applies", "When it applies"]),
    ...when((m.validation || []).length, ["checks", "How to tell it works"]),
    ...when(m.formal_implementation_risk || (m.anti_patterns || []).length, ["looks-done", "Looks done, isn't"]),
    ...when(m.failure_behavior, ["breaks", "When it breaks"]),
    ...when(m.locus || m.control_mechanism, ["sits", "Where it sits"]),
    ...when(m.telemetry, ["records", "What it records"]),
    ...when(asked.length, ["asked", "Asked for"]),
    ...when((m.faq || []).length, ["faq", "Questions"]),
  ];
  return (
    <Shell title={m.name} rail={<LibRail kind="controls" current={m.id} threats={t.threats} controls={all.mitigations} />} side={<Toc items={toc} />}>
      <Saved />
      <nav className="crumbs" aria-label="Breadcrumb">
        {from && <><Link to={from.to} className="from">← {clip(from.title, 60)}</Link><span className="sep" /></>}
        <Link to="/controls">Controls</Link><span>/</span><span className="id" aria-current="page">{m.id}</span>
      </nav>
      <Head title={m.name} meta={[CLASS[m.mitigation_class] || m.mitigation_class, m.failure_behavior ? failText(m.failure_behavior.value) : null, plural(closes.length, "threat") + " it closes"]}
        lede={m.purpose && <p className="lede quiet">{m.purpose}</p>} actions={<Link className="btn" to={`/controls/${m.id}/edit`}><EditIcon />Edit control</Link>} />
      {/* Which threats it answers comes first: it is the reason to read the rest, and the way back. */}
      <section id="closes"><h2>Closes · {closes.length}</h2>
        {closes.length ? <table className="tbl"><tbody>{closes.map(({ t, l }) =>
          <tr key={t.id}><td style={{ width: "45%" }}><Link className="rlink" to={`/threats/${t.id}`}>{t.title}</Link><div className="t3 small">{l.strength === "gating" ? "Stops it" : "Reduces it"} · {harmLabel(t.harm)}</div></td><td className="t2" style={{ fontSize: 14 }}>{l.rationale}</td></tr>)}</tbody></table>
          : <p className="t2">No threat links to it yet. <Link to={`/controls/${m.id}/edit`}>Link one</Link>.</p>}</section>
      {m.scope || m.out_of_scope ? <div className="cols2" id="applies">
        <div className="panel"><h3>Applies when</h3>{m.scope ? <Md text={m.scope} /> : <p className="t3">Not written yet.</p>}</div>
        <div className="panel"><h3>Does not cover</h3>{m.out_of_scope ? <Md text={m.out_of_scope} /> : <p className="t3">Not written yet.</p>}</div>
      </div> : null}
      {(m.validation || []).length > 0 && <section id="checks"><h2>How to tell it works · {m.validation!.length}</h2><p className="sub">Checks a reviewer can run. The core ones must hold for it to count at all.</p>
        <ul className="checks">{m.validation!.map((v, i) => <li key={i}><span className="box" /><span>{v.base && <b>Core. </b>}{v.criterion}</span></li>)}</ul></section>}
      {gaps.length > 0 && <p className="call quiet" style={{ marginBottom: 32 }}><b>Not written yet</b>This card does not yet say {gaps.length > 1 ? gaps.slice(0, -1).join(", ") + " or " + gaps[gaps.length - 1] : gaps[0]}. <Link to={`/controls/${m.id}/edit`}>Add {gaps.length > 1 ? "them" : "it"}</Link>.</p>}
      {(m.formal_implementation_risk || (m.anti_patterns || []).length > 0) && <section id="looks-done"><h2>Looks done, isn't</h2>
        {m.formal_implementation_risk && <div className="call warn"><b>The usual failure</b>{m.formal_implementation_risk}</div>}
        <ul className="qa">{(m.anti_patterns || []).map((a, i) => <li key={i}>{a}</li>)}</ul></section>}
      {m.failure_behavior && <section id="breaks"><h2>When it breaks</h2><p className="prose"><b>{failText(m.failure_behavior.value)}.</b> {m.failure_behavior.note}</p></section>}
      {(m.locus || m.control_mechanism || requires.length > 0) && <section id="sits"><h2>Where it sits</h2>{m.locus && <p className="prose">{m.locus.note}</p>}<Md text={m.control_mechanism} />
        {requires.length > 0 && <p className="prose"><b>Needs in place first: </b>{requires.map((r, i) => <span key={r}>{i ? ", " : ""}<Link to={`/controls/${r}`}>{names[r]?.name || r}</Link></span>)}</p>}</section>}
      {m.telemetry && <section id="records"><h2>What it records</h2><table className="tbl"><thead><tr><th style={{ width: 200 }}>Event</th><th>What it records</th></tr></thead><tbody>
        {m.telemetry.events.map((e) => <tr key={e.name}><td className="where" data-l="Event">{e.name}</td><td>{e.records}<div className="t3 small" style={{ marginTop: 4 }}>{e.attributes.join(" · ")}</div></td></tr>)}</tbody></table>
        <p className="t2" style={{ marginTop: 10, fontSize: 14 }}>{m.telemetry.evidence}</p></section>}
      {asked.length > 0 && <section id="asked"><h2>Asked for in assessments</h2><table className="tbl"><tbody>{asked.map(({ r, f, q }, i) =>
        <tr key={i}><td><Link className="rlink" to={`/reports/${r.system_id}/${r.date}/${f.id}`}>{r.system_name}</Link></td><td><Grade f={f} /></td><td>{q.coverage_status === "needs_implementation" ? "Not built" : q.coverage_status === "partial" ? "Partly in place" : "In place"}</td></tr>)}</tbody></table></section>}
      {(m.faq || []).length > 0 && <section id="faq"><h2>Questions</h2>{m.faq!.map((x, i) => <details className="det" key={i}><summary>{x.question}</summary><p className="prose">{x.answer}</p></details>)}</section>}
      <Step ids={sorted.map((x) => ({ id: x.id, title: x.name }))} current={m.id} base="/controls" label={`Step through ${sorted.length} controls`} />
    </Shell>
  );
}
