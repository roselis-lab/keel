import { useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router";
import { forget, MITIGATIONS, send, THREATS, useApi, type SendError } from "../lib/api";
import type { Mitigation, Report, Threat } from "../lib/types";
import { cap, STATUS } from "../lib/text";
import { Head, Loading, Problem, Shell } from "../components/ui";
import { Area, type Ctx, type Draft, Field, Pick, Seg, Select, SaveBar, setIn, Text, useCheck, useLeaveGuard, useOpenAt, type Vocab, byPath } from "./Editor";

/* A report, edited in the app. The same page shape as the threat editor: the report's own
   headings, one field per thing the old single-file editor let you change, the server's
   validator as you type, and one save bar at the foot. A save writes the whole document
   (the report is one file); saving a final report makes it a draft again, and the report
   page says so. Finalizing is on the report page, where you read what you sign. */

const LEVELS: [string, string][] = [["low", "Low"], ["medium", "Medium"], ["high", "High"]];

export function ReportEditor() {
  const { system, date } = useParams();
  const q = useApi<[Report, { threats: Threat[] }, { mitigations: Mitigation[] }, Vocab]>(`/reports/${system}/${date}`, THREATS, MITIGATIONS, "/vocabulary");
  if (q.loading) return <Shell title="Edit report"><Loading /></Shell>;
  if (q.error) return <Shell title="Edit report"><Problem error={q.error} what="report" /></Shell>;
  return <ReportForm key={`${system}/${date}`} init={q.data[0]} threats={q.data[1].threats} ctrls={q.data[2].mitigations} vocab={q.data[3]} />;
}

function ReportForm({ init, threats, ctrls, vocab }: { init: Report; threats: Threat[]; ctrls: Mitigation[]; vocab: Vocab }) {
  const nav = useNavigate();
  const start = useMemo<Draft>(() => init as unknown as Draft, [init]);
  const [d, setD] = useState<Draft>(start);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const dirty = JSON.stringify(d) !== JSON.stringify(start);
  const guard = useLeaveGuard(dirty);
  useOpenAt();
  const base = `/reports/${init.system_id}/${init.date}`;
  const chk = useCheck(`${base}/validate`, () => d, d);
  const set = (p: string, v: unknown) => { setD((x) => setIn(x, p, v)); setErr(null); chk.touch(p); };
  const c: Ctx = { d, set, errs: chk.shown, advice: {} };
  const tById = Object.fromEntries(threats.map((t) => [t.id, t]));
  const cById = Object.fromEntries(ctrls.map((m) => [m.id, m]));
  const v = (k: string) => Object.entries(vocab[k] || {}).map(([val, x]) => [val, x.name] as [string, string]);
  const findings: Draft[] = d.findings || [];
  const have = new Set(findings.map((f) => f.id));
  const whole = chk.shown._ || [];
  const advice = chk.advice._ || [];

  const blankFinding = (id: string, t?: Threat): Draft => ({
    id, from_catalog: !!t, scenario: "",
    source: { who: t?.source[0] || Object.keys(vocab.source || {})[0] || "external-attacker", motive: "", access: "" },
    asset: "", attack_surface: null, vulnerability: "", exploitation_complexity: "medium",
    harm: t?.harm || Object.keys(vocab.harm || {})[0] || "data-exposed",
    risk: { likelihood: "medium", severity: "medium", reasoning: "" }, delta: "", requirements: [], ignored_mitigations: [],
  });
  const add = (f: Draft) => { set("findings", [...findings, f]); setTimeout(() => document.querySelectorAll(".fcard.finding")[findings.length]?.scrollIntoView({ block: "start" }), 50); };

  async function save() {
    chk.setTried(true);
    if (chk.problems) { setTimeout(() => document.querySelector(".fld.bad, .call.warn")?.scrollIntoView({ block: "center" }), 0); return; }
    setBusy(true); setErr(null);
    try {
      const saved = await send<Report>("PUT", base, d);
      forget("/reports");
      guard.release();
      nav(base, { state: { saved: init.status === "final" && saved.status === "draft" ? "Saved. The report is a draft again: finalize it when you are done." : "Report saved." } });
    } catch (e) {
      const se = e as SendError;
      chk.setErrs(byPath(se.fields || [])); setErr(se.message + (se.hint ? ` — ${se.hint}` : "")); setBusy(false);
    }
  }

  return (
    <Shell title={`Edit ${init.system_name}`}>
      <nav className="crumbs" aria-label="Breadcrumb"><Link to="/reports">Reports</Link><span>/</span><Link to={base}>{init.system_name}</Link><span>/</span><span aria-current="page">Edit</span></nav>
      <Head title={`Edit ${init.system_name}`} meta={[<span className={`status ${init.status}`} key="s">{cap(init.status)}</span>, <span className="num" key="d">Assessed {init.date}</span>, `reports/${init.system_id}/${init.date}.yaml`]}
        lede={init.status === "final" ? <p className="lede quiet">This report is final. Saving a change makes it a draft again, and it needs finalizing once more. To assess the system again rather than correct this record, <Link to="/reports/new">start a new report</Link>.</p> : undefined} />
      {err && <div className="call warn" role="alert"><b>Not saved</b>{err}</div>}
      {!err && whole.length > 0 && <div className="call warn" role="alert"><b>{whole.length === 1 ? "One thing to fix before it saves" : `${whole.length} things to fix before it saves`}</b><ul className="plain">{whole.map((m, i) => <li key={i}>{m}</li>)}</ul></div>}
      <form className="form" onSubmit={(e) => { e.preventDefault(); save(); }}>
        <section id="system"><h2>The system</h2>
          <Field c={c} path="system_description" label="What it does"><Area c={c} path="system_description" rows={5} /></Field>
          <Field c={c} path="delta_summary" label="What changed since the last assessment" optional><Area c={c} path="delta_summary" rows={3} ph="Re-assessments only: what changed and why" /></Field>
        </section>
        <section id="risks"><h2>Risks · {findings.length}</h2>
          <p className="sub">Each risk as the report states it. The grades go first: they decide where it sits in the report.</p>
          <div className="frep">
            {findings.map((f, i) => <FindingCard key={i} c={c} f={f} i={i} t={tById[f.id]} cById={cById} v={v}
              onDrop={() => set("findings", findings.filter((_, j) => j !== i))} />)}
            <Pick id="thr-pick" options={[...threats].sort((a, b) => a.title.localeCompare(b.title)).map((t) => ({ id: t.id, label: `${t.title} · ${t.id}` }))} exclude={have}
              ph="+ Add a risk from the library: type a threat's title" onPick={(tid) => add(blankFinding(tid, tById[tid]))} />
            <p className="small"><button type="button" className="linkbtn" onClick={() => add(blankFinding("T-"))}>+ Add a risk the library does not have</button></p>
          </div>
        </section>
        {advice.length > 0 && <section id="advice"><details className="det"><summary>Worth a look · {advice.length} <span className="t2" style={{ fontWeight: 400 }}>— advice, never blocks a save</span></summary>
          <ul className="plain">{advice.map((m, i) => <li key={i} className="fadv">{m}</li>)}</ul></details></section>}
      </form>
      <SaveBar dirty={dirty} busy={busy} problems={chk.problems} error={err} what="report" onSave={save} leaving={guard.blocker}
        onCancel={() => nav(base)} />
    </Shell>
  );
}

function FindingCard({ c, f, i, t, cById, v, onDrop }: { c: Ctx; f: Draft; i: number; t?: Threat; cById: Record<string, Mitigation>; v: (k: string) => [string, string][]; onDrop: () => void }) {
  const p = `findings.${i}`;
  const [sure, setSure] = useState(false);
  return <div className="fcard finding" id={`risk-${i}`}>
    <div className="fcard-h">
      <span>{t ? <Link to={`/threats/${t.id}`} target="_blank">{t.title}</Link> : f.from_catalog ? f.id : "A risk the library does not have"} {f.id && <span className="id">{f.id}</span>}</span>
      {sure
        ? <span className="small">Remove this risk from the report? <button type="button" className="linkbtn" onClick={onDrop}>Remove</button> · <button type="button" className="linkbtn" onClick={() => setSure(false)}>Keep</button></span>
        : <button type="button" className="fdel" aria-label="Remove this risk" title="Remove this risk" onClick={() => setSure(true)}>×</button>}
    </div>
    {!f.from_catalog && <Field c={c} path={`${p}.id`} label="Id"><Text c={c} path={`${p}.id`} mono ph="T-SHORT-NAME" /></Field>}
    <div className="frow">
      <Field c={c} path={`${p}.risk.severity`} label="Severity"><Seg c={c} path={`${p}.risk.severity`} opts={LEVELS} /></Field>
      <Field c={c} path={`${p}.risk.likelihood`} label="Likelihood"><Seg c={c} path={`${p}.risk.likelihood`} opts={LEVELS} /></Field>
    </div>
    <Field c={c} path={`${p}.risk.reasoning`} label="Why these grades"><Area c={c} path={`${p}.risk.reasoning`} rows={3} ph="A full sentence: what makes it this severe and this likely here" /></Field>
    <Field c={c} path={`${p}.scenario`} label="What happens"><Area c={c} path={`${p}.scenario`} rows={4} /></Field>
    <div className="frow">
      <Field c={c} path={`${p}.source.who`} label="Who could do it"><Select c={c} path={`${p}.source.who`} opts={v("source")} /></Field>
      <Field c={c} path={`${p}.harm`} label="Harm"><Select c={c} path={`${p}.harm`} opts={v("harm")} /></Field>
    </div>
    <div className="frow">
      <Field c={c} path={`${p}.source.motive`} label="Their goal, or what triggers it"><Area c={c} path={`${p}.source.motive`} rows={2} /></Field>
      <Field c={c} path={`${p}.source.access`} label="Their access or permissions"><Area c={c} path={`${p}.source.access`} rows={2} /></Field>
    </div>
    <div className="frow">
      <Field c={c} path={`${p}.asset`} label="What is at stake"><Area c={c} path={`${p}.asset`} rows={2} /></Field>
      <Field c={c} path={`${p}.attack_surface`} label="Way in" optional><Select c={c} path={`${p}.attack_surface`} blank="None: the weakness stands on its own" opts={v("surface")} /></Field>
    </div>
    <Field c={c} path={`${p}.vulnerability`} label="What lets it happen"><Area c={c} path={`${p}.vulnerability`} rows={2} /></Field>
    <div className="frow">
      <Field c={c} path={`${p}.exploitation_complexity`} label="Effort to exploit"><Seg c={c} path={`${p}.exploitation_complexity`} opts={LEVELS} /></Field>
      <Field c={c} path={`${p}.delta`} label="Since last time"><Area c={c} path={`${p}.delta`} rows={2} /></Field>
    </div>
    {(f.requirements || []).length > 0 && <div className="fld"><span className="fl">Fixed by · {f.requirements.length}</span>
      <p className="fh">Ticked fixes go to the team that owns the system when you share the report.</p>
      {(f.requirements as Draft[]).map((r, ri) => { const rp = `${p}.requirements.${ri}`; const ctl = r.mitigation_id ? cById[r.mitigation_id] : undefined;
        return <div className="fcard" key={ri}>
          <label className="fcheck"><input type="checkbox" checked={!!r.included} onChange={(e) => c.set(`${rp}.included`, e.target.checked)} /> <b>{ctl?.name || r.description || r.mitigation_id || "A fix written for this system"}</b> <span className="t2 small">· {STATUS[r.coverage_status] || r.coverage_status}</span></label>
          {r.coverage_note && <p className="t2 small">{r.coverage_note}</p>}
          <Field c={c} path={`${rp}.invariant`} label="Must always hold" optional><Area c={c} path={`${rp}.invariant`} rows={2} /></Field>
          <div className="frow">
            <Field c={c} path={`${rp}.enforce_at`} label="Enforce at" optional><Area c={c} path={`${rp}.enforce_at`} rows={2} /></Field>
            <Field c={c} path={`${rp}.done_check`} label="Done when" optional><Area c={c} path={`${rp}.done_check`} rows={2} /></Field>
          </div>
        </div>; })}
    </div>}
  </div>;
}

/** /reports/new — the by-hand start: an empty draft dated today, then its editor. Most
    reports are written by the assessment skill instead. */
export function NewReport() {
  const nav = useNavigate();
  const [d, setD] = useState<Draft>({ system_name: "", system_id: "", system_description: "" });
  const [ownId, setOwnId] = useState(false);
  const [errs, setErrs] = useState<Record<string, string[]>>({});
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const dirty = !!(d.system_name || d.system_id || d.system_description);
  const guard = useLeaveGuard(dirty);
  // The id follows the name until you type one yourself: nobody wants to type the same
  // words twice in two shapes.
  const slug = (s: string) => s.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
  const set = (p: string, val: unknown) => {
    setD((x) => { const n = setIn(x, p, val); if (p === "system_name" && !ownId) n.system_id = slug(String(val)); return n; });
    if (p === "system_id") setOwnId(true);
    setErr(null); setErrs((e) => { const n = { ...e }; delete n[p]; if (p === "system_name") delete n.system_id; return n; });
  };
  const local = { ...errs, ...(d.system_id && !/^[a-z0-9]+(-[a-z0-9]+)*$/.test(d.system_id) ? { system_id: ["Lowercase letters, digits and hyphens: checkout-agent."] } : {}) };
  const c: Ctx = { d, set, errs: local, advice: {} };
  async function create() {
    if (!d.system_name.trim() || !d.system_id) { setErrs({ ...(d.system_name.trim() ? {} : { system_name: ["Required."] }), ...(d.system_id ? {} : { system_id: ["Required."] }) }); return; }
    setBusy(true); setErr(null);
    try {
      const r = await send<Report>("POST", "/reports", d);
      forget("/reports"); guard.release();
      nav(`/reports/${r.system_id}/${r.date}/edit`);
    } catch (e) {
      const se = e as SendError;
      setErrs(byPath(se.fields || [])); setErr(se.message + (se.hint ? ` — ${se.hint}` : "")); setBusy(false);
    }
  }
  return (
    <Shell title="New report">
      <nav className="crumbs" aria-label="Breadcrumb"><Link to="/reports">Reports</Link><span>/</span><span aria-current="page">New</span></nav>
      <Head title="Assess a system" lede={<p className="lede quiet">Creates an empty draft dated today, which you then fill in. Most reports come from the assessment skill instead: it writes this file for you.</p>} />
      {err && <div className="call warn" role="alert"><b>Not created</b>{err}</div>}
      <form className="form" onSubmit={(e) => { e.preventDefault(); create(); }}>
        <section><h2>The system</h2>
          <Field c={c} path="system_name" label="Name"><Text c={c} path="system_name" ph="Checkout Agent" /></Field>
          <Field c={c} path="system_id" label="Id"><Text c={c} path="system_id" mono ph="checkout-agent" /><p className="fh">It becomes the folder under reports/, so it stays with the system for good.</p></Field>
          <Field c={c} path="system_description" label="What it does" optional><Area c={c} path="system_description" rows={3} ph="Answers storefront checkout questions and issues refunds under a value cap." /><p className="fh">A later assessment matches against this to recognise the same system.</p></Field>
        </section>
      </form>
      <SaveBar dirty={dirty} busy={busy} problems={Object.values(local).flat().length} error={err} what="report" verb="Create draft" onSave={create} leaving={guard.blocker} onCancel={() => nav("/reports")} />
    </Shell>
  );
}
