import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { Link, useBlocker, useNavigate, useParams, type Blocker } from "react-router";
import { forget, MITIGATIONS, send, THREATS, useApi, type FieldError, type SendError } from "../lib/api";
import type { Mitigation, Threat } from "../lib/types";
import { cap, CLASS, firstSentence, harmLabel } from "../lib/text";
import { Head, Loading, Problem, Shell } from "../components/ui";

/* The library editor, in the app. One page per record, laid out in the same order and
   under the same headings as the card it edits, so the reader finds a field where they
   last read it. Everything is saved in one go by the bar at the foot of the screen; the
   only immediate writes are links made from a control to a threat, because a link is
   stored on the threat and the control's own Save cannot carry it. */

type Vocab = Record<string, Record<string, { name: string; desc: string }>>;
type Guide = { entities: Record<string, { fields: Record<string, { purpose?: string; content_requirements?: string[]; avoid?: string[] }> }> };
type Schema = { properties: Record<string, unknown>; $defs?: Record<string, { properties: Record<string, unknown> }> };
type Draft = Record<string, any>; // eslint-disable-line @typescript-eslint/no-explicit-any

/** The allowed values of a field, read from the JSON schema so the form never drifts from it. */
function enumOf(s: Schema | undefined, ...path: string[]): string[] {
  let node: any = s; // eslint-disable-line @typescript-eslint/no-explicit-any
  for (const p of path) {
    if (!node) return [];
    if (node.anyOf) node = node.anyOf.find((x: { type?: string }) => x.type !== "null");
    if (node?.$ref) node = s?.$defs?.[node.$ref.split("/").pop()];
    if (node?.items) node = node.items;
    node = node?.properties?.[p] ?? node?.[p];
  }
  if (node?.anyOf) node = node.anyOf.find((x: { type?: string }) => x.type !== "null");
  if (node?.items) node = node.items;
  return node?.enum || [];
}

const get = (o: Draft, path: string) => path.split(".").reduce<any>((a, k) => (a == null ? a : a[k]), o); // eslint-disable-line @typescript-eslint/no-explicit-any
function setIn(o: Draft, path: string, v: unknown): Draft {
  const [k, ...rest] = path.split(".");
  const key: string | number = Array.isArray(o) ? Number(k) : k;
  const copy: any = Array.isArray(o) ? [...o] : { ...o }; // eslint-disable-line @typescript-eslint/no-explicit-any
  copy[key] = rest.length ? setIn(copy[key] ?? (/^\d+$/.test(rest[0]) ? [] : {}), rest.join("."), v) : v;
  return copy;
}

/* ---------- field shell: label, one-line why, the input, then its errors and advice ---------- */

interface Ctx { d: Draft; set: (p: string, v: unknown) => void; errs: Record<string, string[]>; advice: Record<string, string[]>; guide?: Guide }

function Field({ c, path, label, entity, name, children, optional }: { c: Ctx; path: string; label: string; entity?: string; name?: string; children: ReactNode; optional?: boolean }) {
  const g = entity && name ? c.guide?.entities?.[entity]?.fields?.[name] : undefined;
  const errs = c.errs[path] || [], adv = c.advice[path] || [];
  const more = [...(g?.content_requirements || []), ...(g?.avoid || []).map((a) => "Avoid: " + a)];
  return (
    <div className={`fld${errs.length ? " bad" : ""}`} data-path={path}>
      <label className="fl" htmlFor={`f-${path}`}>{label}{optional && <span className="opt"> · optional</span>}</label>
      {g?.purpose && <p className="fh">{firstSentence(g.purpose)}</p>}
      {children}
      {errs.map((e, i) => <p key={i} className="ferr" role="alert">{e}</p>)}
      {adv.map((e, i) => <p key={i} className="fadv">{e}</p>)}
      {more.length > 0 && <details className="fmore"><summary>How to write it</summary><ul>{more.map((m, i) => <li key={i}>{m}</li>)}</ul></details>}
    </div>
  );
}

const Text = ({ c, path, ph, mono }: { c: Ctx; path: string; ph?: string; mono?: boolean }) =>
  <input id={`f-${path}`} className={`fi${mono ? " mono" : ""}`} value={get(c.d, path) ?? ""} placeholder={ph} onChange={(e) => c.set(path, e.target.value)} />;
const Area = ({ c, path, ph, rows = 3 }: { c: Ctx; path: string; ph?: string; rows?: number }) =>
  <textarea id={`f-${path}`} className="fi" rows={rows} value={get(c.d, path) ?? ""} placeholder={ph} onChange={(e) => c.set(path, e.target.value)} />;
function Select({ c, path, opts, blank }: { c: Ctx; path: string; opts: [string, string][]; blank?: string }) {
  return <select id={`f-${path}`} className="fi" value={get(c.d, path) ?? ""} onChange={(e) => c.set(path, e.target.value)}>
    {blank !== undefined && <option value="">{blank}</option>}
    {opts.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
  </select>;
}
function Checks({ c, path, opts }: { c: Ctx; path: string; opts: [string, string, string?][] }) {
  const on = new Set<string>(get(c.d, path) || []);
  return <div className="fchecks" role="group">{opts.map(([v, l, t]) =>
    <label key={v} title={t}><input type="checkbox" checked={on.has(v)} onChange={() => { const n = new Set(on); n.has(v) ? n.delete(v) : n.add(v); c.set(path, opts.map(([x]) => x).filter((x) => n.has(x))); }} />{l}</label>)}</div>;
}
/** Choose one of two or three, every option visible: one click, nothing hidden in a menu. */
function Seg({ c, path, opts }: { c: Ctx; path: string; opts: [string, string][] }) {
  const v = get(c.d, path);
  return <div className="toggle fseg" role="radiogroup">{opts.map(([k, l]) => <button type="button" role="radio" key={k} aria-checked={v === k} aria-pressed={v === k} onClick={() => c.set(path, k)}>{l}</button>)}</div>;
}

/** A list of cards, each one item. Add at the foot, remove with the cross on the card. */
function Repeat({ c, path, blank, add, head, children }: { c: Ctx; path: string; blank: () => Draft; add: string; head: (it: Draft, i: number) => ReactNode; children: (p: string, i: number) => ReactNode }) {
  const items: Draft[] = get(c.d, path) || [];
  return <div className="frep">
    {items.map((it, i) => <div className="fcard" key={i}>
      <div className="fcard-h"><span>{head(it, i)}</span><button type="button" className="fdel" aria-label="Remove" title="Remove" onClick={() => c.set(path, items.filter((_, j) => j !== i))}>×</button></div>
      {children(`${path}.${i}`, i)}
    </div>)}
    <button type="button" className="btn" onClick={() => c.set(path, [...items, blank()])}>+ {add}</button>
  </div>;
}

/** A plain list of one-line strings (anti-patterns). */
function Lines({ c, path, add, ph }: { c: Ctx; path: string; add: string; ph?: string }) {
  const items: string[] = get(c.d, path) || [];
  return <div className="frep">
    {items.map((_, i) => <div className="fline" key={i}><Area c={c} path={`${path}.${i}`} rows={2} ph={ph} /><button type="button" className="fdel" aria-label="Remove" title="Remove" onClick={() => c.set(path, items.filter((_, j) => j !== i))}>×</button></div>)}
    <button type="button" className="btn" onClick={() => c.set(path, [...items, ""])}>+ {add}</button>
  </div>;
}

/** Pick a record by typing part of its name or id; the browser's own list does the filtering. */
function Pick({ id, options, onPick, ph, exclude }: { id: string; options: { id: string; label: string }[]; onPick: (id: string) => void; ph: string; exclude?: Set<string> }) {
  const [v, setV] = useState("");
  const list = options.filter((o) => !exclude?.has(o.id));
  const go = (s: string) => { const hit = list.find((o) => o.label === s || o.id === s); if (hit) { onPick(hit.id); setV(""); } else setV(s); };
  return <div className="fpick">
    <input className="fi" list={id} value={v} placeholder={ph} onChange={(e) => go(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); const hit = list.find((o) => o.label.toLowerCase().includes(v.toLowerCase())); if (hit) go(hit.label); } }} />
    <datalist id={id}>{list.map((o) => <option key={o.id} value={o.label} />)}</datalist>
  </div>;
}

/* ---------- saving: one bar at the foot, always in the same place ---------- */

function SaveBar({ dirty, busy, problems, onSave, onCancel, onDelete, what, error, leaving }: { dirty: boolean; busy: boolean; problems: number; onSave: () => void; onCancel: () => void; onDelete?: () => void; what: string; error?: string | null; leaving: Blocker }) {
  const [sure, setSure] = useState(false);
  if (leaving.state === "blocked") return <div className="savebar" role="region" aria-label="Save">
    <div className="savebar-in">
      <span className="sb-state bad" role="alert">Leave without saving? Your changes to this {what} will be lost.</span>
      <button type="button" className="btn" onClick={() => leaving.proceed()}>Leave</button>
      <button type="button" className="btn solid" autoFocus onClick={() => leaving.reset()}>Stay</button>
    </div>
  </div>;
  return <div className="savebar" role="region" aria-label="Save">
    <div className="savebar-in">
      <span className={`sb-state${error ? " bad" : ""}`} role="status">{error ? error : busy ? "Saving…" : problems ? `${problems} to fix before it saves` : dirty ? "Unsaved changes" : "No changes"}</span>
      {onDelete && (sure
        ? <span className="sb-sure">Delete this {what} for good? <button type="button" className="btn danger" onClick={onDelete}>Delete</button> <button type="button" className="btn" onClick={() => setSure(false)}>Keep</button></span>
        : <button type="button" className="sb-del" onClick={() => setSure(true)}>Delete {what}</button>)}
      <button type="button" className="btn" onClick={onCancel}>{dirty ? "Discard" : "Close"}</button>
      <button type="button" className="btn solid" disabled={busy || !dirty} onClick={onSave}>Save</button>
    </div>
  </div>;
}

/** Unsaved changes stop every way out: closing the tab, and any link in the app (top
 * menu, breadcrumb, Discard), which then asks in the save bar. `release` lets a finished
 * save or delete through. */
function useLeaveGuard(dirty: boolean) {
  const free = useRef(false);
  useEffect(() => {
    if (!dirty) return;
    const h = (e: BeforeUnloadEvent) => { e.preventDefault(); };
    addEventListener("beforeunload", h);
    return () => removeEventListener("beforeunload", h);
  }, [dirty]);
  const blocker = useBlocker(({ currentLocation, nextLocation }) => dirty && !free.current && currentLocation.pathname !== nextLocation.pathname);
  return { blocker, release: () => { free.current = true; } };
}

/** The validator's wording names the allowed tokens; on a form the options are right there. */
function plainMsg(m: string) {
  if (/^Input should be '/.test(m)) return "Choose one of the options.";
  if (m === "Field required") return "Required.";
  if (/^String should have at least 1 character/.test(m)) return "Required.";
  if (/^List should have at least 1 item/.test(m)) return "Add at least one.";
  if (/^Input should be a valid URL/.test(m)) return "A full link, starting with https://.";
  return m.replace(/^Value error, /, "");
}
const byPath = (xs: FieldError[]) => xs.reduce<Record<string, string[]>>((a, e) => { (a[e.field || "_"] ||= []).push(plainMsg(e.msg)); return a; }, {});
const blankStr = (v: unknown) => (typeof v === "string" && !v.trim() ? null : v);

/* ---------- threat ---------- */

const THREAT_KEYS = ["title", "harm", "source", "weaknesses", "reachability", "mitigations", "references", "positioning", "tags"];

function cleanThreat(d: Draft) {
  const out: Draft = {};
  for (const k of THREAT_KEYS) out[k] = d[k];
  out.positioning = blankStr(out.positioning);
  out.tags = String(d.tagsText ?? (d.tags || []).join(", ")).split(",").map((s) => s.trim()).filter(Boolean);
  out.mitigations = (d.mitigations || []).map((m: Draft) => ({ ...m, exception: blankStr(m.exception) }));
  return out;
}

export function ThreatEditor() {
  const { id } = useParams();
  const isNew = !id;
  const q = useApi<[Threat | null, { mitigations: Mitigation[] }, Vocab, Guide, Schema]>(isNew ? null : `/threats/${id}`, MITIGATIONS, "/vocabulary", "/style-guide", "/schema/threat");
  if (q.loading) return <Shell title="Edit threat"><Loading /></Shell>;
  if (q.error) return <Shell title="Edit threat"><Problem error={q.error} what="threat" /></Shell>;
  return <ThreatForm key={id || "new"} init={q.data[0]} ctrls={q.data[1].mitigations} vocab={q.data[2]} guide={q.data[3]} schema={q.data[4]} />;
}

function ThreatForm({ init, ctrls, vocab, guide, schema }: { init: Threat | null; ctrls: Mitigation[]; vocab: Vocab; guide: Guide; schema: Schema }) {
  const nav = useNavigate();
  const isNew = !init;
  const start = useMemo<Draft>(() => init ? { ...init, tagsText: ((init as Draft).tags || []).join(", ") }
    : { id: "T-", title: "", harm: "", source: [], weaknesses: [{ component: "", surface: [], text: "", nature: "targeted" }], reachability: "", mitigations: [], references: [], positioning: "", tagsText: "" }, [init]);
  const [d, setD] = useState<Draft>(start);
  const [errs, setErrs] = useState<Record<string, string[]>>({});
  const [advice, setAdvice] = useState<Record<string, string[]>>({});
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [touched, setTouched] = useState<string[]>([]);
  const [tried, setTried] = useState(false);
  const dirty = JSON.stringify(d) !== JSON.stringify(start);
  const guard = useLeaveGuard(dirty);
  const set = (p: string, v: unknown) => { setD((x) => setIn(x, p, v)); setErr(null); setTouched((t) => (t.includes(p) ? t : [...t, p])); };
  // A field says what is wrong once it has been touched, or after a save was tried:
  // a new record should not open as a page of red.
  const near = (a: string, b: string) => a === b || a.startsWith(b + ".") || b.startsWith(a + ".");
  const shown = Object.fromEntries(Object.entries(errs).filter(([p]) => tried || touched.some((t) => near(p, t === "tagsText" ? "tags" : t))));
  const c: Ctx = { d, set, errs: shown, advice, guide };

  // The server's own validator, so the form says what a save would say, as you type.
  const timer = useRef<number>(0);
  useEffect(() => {
    window.clearTimeout(timer.current);
    timer.current = window.setTimeout(() => {
      send<{ ok: boolean; errors: FieldError[]; advice: FieldError[] }>("POST", "/threats/validate", { id: d.id, ...cleanThreat(d) })
        .then((r) => { setErrs(byPath(r.errors)); setAdvice(byPath(r.advice)); }).catch(() => {});
    }, 450);
    return () => window.clearTimeout(timer.current);
  }, [d]); // eslint-disable-line react-hooks/exhaustive-deps

  const v = (k: string) => Object.entries(vocab[k] || {}).map(([val, x]) => [val, x.name, x.desc] as [string, string, string]);
  const ctrlById = Object.fromEntries(ctrls.map((m) => [m.id, m]));
  const ctrlOpts = [...ctrls].sort((a, b) => a.name.localeCompare(b.name)).map((m) => ({ id: m.id, label: `${m.name} · ${m.id}` }));
  const linked = new Set<string>((d.mitigations || []).map((m: Draft) => m.id));
  const problems = Object.values(errs).flat().length;

  async function save() {
    setTried(true);
    if (problems) { setTimeout(() => document.querySelector(".fld.bad")?.scrollIntoView({ block: "center" }), 0); return; }
    setBusy(true); setErr(null);
    try {
      const body = cleanThreat(d);
      const saved = await send<Threat>(isNew ? "POST" : "PATCH", isNew ? "/threats" : `/threats/${init!.id}`, isNew ? { id: d.id, ...body } : changed(body, cleanThreat(start)));
      forget("/threats"); forget("/reports");
      guard.release();
      nav(`/threats/${saved.id || d.id}`, { state: { saved: true } });
    } catch (e) {
      const se = e as SendError;
      setErrs(byPath(se.fields || [])); setErr(se.message + (se.hint ? ` — ${se.hint}` : "")); setBusy(false);
    }
  }
  async function del() {
    setBusy(true);
    try { await send("DELETE", `/threats/${init!.id}`); forget("/threats"); forget("/mitigations"); guard.release(); nav("/threats", { state: { saved: "deleted" } }); }
    catch (e) { setErr((e as Error).message); setBusy(false); }
  }

  const title = isNew ? "New threat" : "Edit threat";
  return (
    <Shell title={title}>
      <nav className="crumbs" aria-label="Breadcrumb"><Link to="/threats">Threats</Link>{!isNew && <><span>/</span><Link to={`/threats/${init!.id}`}>{init!.title}</Link></>}<span>/</span><span aria-current="page">{isNew ? "New" : "Edit"}</span></nav>
      <Head title={title} meta={isNew ? ["Written to catalog/threats/ when you save"] : [<span className="id" key="id">{init!.id}</span>, `catalog/threats/${init!.id}.yaml`]} />
      {err && <div className="call warn" role="alert"><b>Not saved</b>{err}</div>}
      <form className="form" onSubmit={(e) => { e.preventDefault(); save(); }}>
        <section><h2>What goes wrong</h2>
          {isNew && <Field c={c} path="id" label="Id"><Text c={c} path="id" mono ph="T-SHORT-NAME" /><p className="fh">Capital letters, digits and hyphens, starting with T-. It is also the file name and cannot change later.</p></Field>}
          <Field c={c} path="title" label="Title" entity="threat" name="title"><Text c={c} path="title" ph="One sentence: what goes wrong" /></Field>
          <div className="frow">
            <Field c={c} path="harm" label="Harm" entity="threat" name="harm"><Select c={c} path="harm" blank="Choose a harm" opts={v("harm").map(([k, n]) => [k, n])} /></Field>
            <Field c={c} path="source" label="Who causes it" entity="threat" name="source"><Checks c={c} path="source" opts={v("source")} /></Field>
          </div>
        </section>
        <section><h2>Does not apply when</h2>
          <Field c={c} path="reachability" label="The condition that rules it out" entity="threat" name="reachability"><Area c={c} path="reachability" rows={3} ph="The model cannot influence the arguments…" /></Field>
        </section>
        <section><h2>What stops or reduces it · {linked.size}</h2>
          <p className="sub">Each link says why this control answers this threat. Stops it: blocks the path when it holds. Reduces it: only makes it less likely or easier to catch.</p>
          <div className="frep">
            {(d.mitigations || []).map((m: Draft, i: number) => <div className="fcard" key={m.id}>
              <div className="fcard-h"><span><Link to={`/controls/${m.id}`} target="_blank">{ctrlById[m.id]?.name || m.id}</Link> <span className="id">{m.id}</span></span>
                <button type="button" className="fdel" aria-label="Unlink" title="Unlink" onClick={() => set("mitigations", d.mitigations.filter((_: Draft, j: number) => j !== i))}>×</button></div>
              <Field c={c} path={`mitigations.${i}.strength`} label="Role" entity="mitigation_link" name="strength"><Seg c={c} path={`mitigations.${i}.strength`} opts={[["gating", "Stops it"], ["soft", "Reduces it"]]} /></Field>
              <Field c={c} path={`mitigations.${i}.rationale`} label="Why it answers this threat" entity="mitigation_link" name="rationale"><Area c={c} path={`mitigations.${i}.rationale`} rows={2} /></Field>
              <Field c={c} path={`mitigations.${i}.exception`} label="Exception" entity="mitigation_link" name="exception" optional><Area c={c} path={`mitigations.${i}.exception`} rows={2} ph="A narrow case where this control does not apply to this threat" /></Field>
            </div>)}
            <Pick id="ctrl-pick" options={ctrlOpts} exclude={linked} ph="+ Link a control: type its name" onPick={(mid) => set("mitigations", [...(d.mitigations || []), { id: mid, strength: "gating", rationale: "", exception: null }])} />
          </div>
        </section>
        <section><h2>Weak spots · {(d.weaknesses || []).length}</h2>
          <Repeat c={c} path="weaknesses" add="Add a weak spot" blank={() => ({ component: "", surface: [], text: "", nature: "targeted" })}
            head={(w, i) => <>Weak spot {i + 1}{w.component ? ` · ${vocab.components?.[w.component]?.name || w.component}` : ""}</>}>
            {(p) => <>
              <div className="frow">
                <Field c={c} path={`${p}.component`} label="In which part" entity="weakness" name="component"><Select c={c} path={`${p}.component`} blank="Choose a part" opts={v("components").map(([k, n]) => [k, n])} /></Field>
                <Field c={c} path={`${p}.nature`} label="Role" entity="weakness" name="nature"><Seg c={c} path={`${p}.nature`} opts={enumOf(schema, "weaknesses", "nature").map((k) => [k, k === "targeted" ? "Targeted" : "Secondary"])} /></Field>
              </div>
              <Field c={c} path={`${p}.surface`} label="Reached through" entity="weakness" name="surface" optional><Checks c={c} path={`${p}.surface`} opts={v("surface")} /></Field>
              <Field c={c} path={`${p}.text`} label="The condition" entity="weakness" name="text"><Area c={c} path={`${p}.text`} ph="Cause + where + defect" /></Field>
            </>}
          </Repeat>
        </section>
        <section><h2>Seen in the wild · {(d.references || []).length}</h2>
          <Repeat c={c} path="references" add="Add a source" blank={() => ({ title: "", url: "", note: "" })} head={(r, i) => r.title || `Source ${i + 1}`}>
            {(p) => <>
              <Field c={c} path={`${p}.title`} label="Title"><Text c={c} path={`${p}.title`} /></Field>
              <Field c={c} path={`${p}.url`} label="Link"><Text c={c} path={`${p}.url`} mono ph="https://" /></Field>
              <Field c={c} path={`${p}.note`} label="What it supports"><Area c={c} path={`${p}.note`} rows={2} ph="One line: what this source actually shows" /></Field>
            </>}
          </Repeat>
        </section>
        <section><h2>Against the frameworks</h2>
          <Field c={c} path="positioning" label="How it sits against tracked sources" entity="threat" name="positioning" optional><Area c={c} path="positioning" rows={3} /></Field>
          <Field c={c} path="tags" label="Tags" entity="threat" name="tags" optional><Text c={c} path="tagsText" ph="comma, separated" /></Field>
        </section>
      </form>
      <SaveBar dirty={dirty} busy={busy} problems={problems} error={err} what="threat" onSave={save} leaving={guard.blocker}
        onCancel={() => nav(isNew ? "/threats" : `/threats/${init!.id}`)} onDelete={isNew ? undefined : del} />
    </Shell>
  );
}

/* ---------- control ---------- */

/** An edit sends only the fields that changed, so a save rewrites what you touched and
    nothing else. The server skips nulls in an update, so a cleared text goes as "". */
function changed(body: Draft, base: Draft) {
  const out: Draft = {};
  for (const k of Object.keys(body)) {
    if (JSON.stringify(body[k] ?? null) === JSON.stringify(base[k] ?? null)) continue;
    out[k] = body[k] === null && typeof base[k] === "string" ? "" : body[k];
  }
  return out;
}

function cleanControl(d: Draft, keys: string[]) {
  const out: Draft = {};
  for (const k of keys) if (k !== "id" && k in d) out[k] = d[k];
  for (const k of Object.keys(out)) out[k] = blankStr(out[k]);
  for (const k of ["locus", "failure_behavior"]) if (out[k] && !out[k].value && !String(out[k].note || "").trim()) out[k] = null;
  if (out.telemetry && !(out.telemetry.events || []).length && !String(out.telemetry.evidence || "").trim()) out.telemetry = null;
  else if (out.telemetry) out.telemetry = { ...out.telemetry, evidence: blankStr(out.telemetry.evidence), events: out.telemetry.events.map((e: Draft) => ({ ...e, attributes: Array.isArray(e.attributes) ? e.attributes : String(e.attributes || "").split(",").map((s) => s.trim()).filter(Boolean) })) };
  if (out.validation) out.validation = out.validation.map((x: Draft) => ({ ...x, test_scenario: blankStr(x.test_scenario), expected_result: blankStr(x.expected_result) }));
  if (out.anti_patterns) out.anti_patterns = out.anti_patterns.filter((s: string) => s.trim());
  if (out.implementations) out.implementations = out.implementations.map((x: Draft) => ({ ...x, reference: blankStr(x.reference), covers: blankStr(x.covers), owner: blankStr(x.owner) }));
  return out;
}

export function ControlEditor() {
  const { id } = useParams();
  const isNew = !id;
  const q = useApi<[Mitigation | null, { mitigations: Mitigation[] }, { threats: Threat[] }, Guide, Schema]>(isNew ? null : `/mitigations/${id}`, MITIGATIONS, THREATS, "/style-guide", "/schema/mitigation");
  if (q.loading) return <Shell title="Edit control"><Loading /></Shell>;
  if (q.error) return <Shell title="Edit control"><Problem error={q.error} what="control" /></Shell>;
  return <ControlForm key={id || "new"} init={q.data[0]} ctrls={q.data[1].mitigations} threats={q.data[2].threats} guide={q.data[3]} schema={q.data[4]} />;
}

function ControlForm({ init, ctrls, threats, guide, schema }: { init: Mitigation | null; ctrls: Mitigation[]; threats: Threat[]; guide: Guide; schema: Schema }) {
  const nav = useNavigate();
  const isNew = !init;
  const keys = Object.keys(schema.properties);
  const start = useMemo<Draft>(() => {
    const base: Draft = { id: "CTRL-", name: "", mitigation_class: "", requires: [], validation: [], anti_patterns: [], faq: [] };
    const src: Draft = init ? { ...init } : base;
    const d: Draft = {};
    for (const k of keys) d[k] = src[k] ?? base[k] ?? (k === "implementations" ? [] : null);
    d.locus ||= { value: "", note: "" }; d.failure_behavior ||= { value: "", note: "" };
    d.telemetry ||= { events: [], evidence: "" };
    d.telemetry = { ...d.telemetry, events: (d.telemetry.events || []).map((e: Draft) => ({ ...e, attributes: (e.attributes || []).join(", ") })) };
    return d;
  }, [init]); // eslint-disable-line react-hooks/exhaustive-deps
  const [d, setD] = useState<Draft>(start);
  const [errs, setErrs] = useState<Record<string, string[]>>({});
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const dirty = JSON.stringify(d) !== JSON.stringify(start);
  const guard = useLeaveGuard(dirty);
  const set = (p: string, v: unknown) => { setD((x) => setIn(x, p, v)); setErr(null); setErrs((e) => { const n = { ...e }; delete n[p]; return n; }); };
  const c: Ctx = { d, set, errs, advice: {}, guide };
  const cls = enumOf(schema, "mitigation_class").map((k) => [k, CLASS[k] ? `${CLASS[k]} · ${k.replace(/_/g, " ")}` : k] as [string, string]);
  const otherCtrls = ctrls.filter((m) => m.id !== init?.id).sort((a, b) => a.name.localeCompare(b.name)).map((m) => ({ id: m.id, label: `${m.name} · ${m.id}` }));
  const nameOf = Object.fromEntries(ctrls.map((m) => [m.id, m.name]));

  async function save() {
    setBusy(true); setErr(null);
    try {
      const body = cleanControl(d, keys);
      const saved = await send<Mitigation>(isNew ? "POST" : "PATCH", isNew ? "/mitigations" : `/mitigations/${init!.id}`, isNew ? { id: d.id, ...body } : changed(body, cleanControl(start, keys)));
      forget("/mitigations"); forget("/threats");
      guard.release();
      nav(`/controls/${saved.id || d.id}`, { state: { saved: true } });
    } catch (e) {
      const se = e as SendError;
      setErrs(byPath(se.fields || [])); setErr(se.message + (se.hint ? ` — ${se.hint}` : "")); setBusy(false);
    }
  }
  async function del() {
    setBusy(true);
    try { await send("DELETE", `/mitigations/${init!.id}`); forget("/mitigations"); forget("/threats"); guard.release(); nav("/controls", { state: { saved: "deleted" } }); }
    catch (e) { setErr((e as Error).message); setBusy(false); }
  }

  const title = isNew ? "New control" : "Edit control";
  const decision = (k: "locus" | "failure_behavior", label: string, opts: [string, string][]) =>
    <Field c={c} path={`${k}.value`} label={label} entity="mitigation" name={k} optional>
      <Seg c={c} path={`${k}.value`} opts={opts} />
      <Area c={c} path={`${k}.note`} rows={2} ph="Why, in this control's terms" />
      {(c.errs[`${k}.note`] || []).map((e, i) => <p key={i} className="ferr">{e}</p>)}
    </Field>;
  return (
    <Shell title={title}>
      <nav className="crumbs" aria-label="Breadcrumb"><Link to="/controls">Controls</Link>{!isNew && <><span>/</span><Link to={`/controls/${init!.id}`}>{init!.name}</Link></>}<span>/</span><span aria-current="page">{isNew ? "New" : "Edit"}</span></nav>
      <Head title={title} meta={isNew ? ["Written to catalog/mitigations/ when you save"] : [<span className="id" key="id">{init!.id}</span>, `catalog/mitigations/${init!.id}.yaml`]} />
      {err && <div className="call warn" role="alert"><b>Not saved</b>{err}</div>}
      <form className="form" onSubmit={(e) => { e.preventDefault(); save(); }}>
        <section><h2>What it is</h2>
          {isNew && <Field c={c} path="id" label="Id"><Text c={c} path="id" mono ph="CTRL-SHORT-NAME" /><p className="fh">Capital letters, digits and hyphens, starting with CTRL-. It is also the file name and cannot change later.</p></Field>}
          <Field c={c} path="name" label="Name" entity="mitigation" name="name"><Text c={c} path="name" /></Field>
          <Field c={c} path="mitigation_class" label="Kind" entity="mitigation" name="mitigation_class"><Select c={c} path="mitigation_class" blank="Choose a kind" opts={cls} /></Field>
          <Field c={c} path="purpose" label="Purpose" entity="mitigation" name="purpose"><Area c={c} path="purpose" rows={3} ph="1–3 sentences: which class of failure it prevents" /></Field>
        </section>
        <section><h2>When it applies</h2>
          <div className="frow">
            <Field c={c} path="scope" label="Applies when" entity="mitigation" name="scope"><Area c={c} path="scope" rows={4} /></Field>
            <Field c={c} path="out_of_scope" label="Does not cover" entity="mitigation" name="out_of_scope"><Area c={c} path="out_of_scope" rows={4} /></Field>
          </div>
        </section>
        <section><h2>How to tell it works · {(d.validation || []).length}</h2>
          <Repeat c={c} path="validation" add="Add a check" blank={() => ({ criterion: "", test_scenario: "", expected_result: "", base: true })} head={(x, i) => `Check ${i + 1}${x.base ? " · core" : ""}`}>
            {(p) => <>
              <Field c={c} path={`${p}.criterion`} label="Passes when"><Area c={c} path={`${p}.criterion`} rows={2} /></Field>
              <div className="frow">
                <Field c={c} path={`${p}.test_scenario`} label="How to test" optional><Area c={c} path={`${p}.test_scenario`} rows={2} /></Field>
                <Field c={c} path={`${p}.expected_result`} label="Expected result" optional><Area c={c} path={`${p}.expected_result`} rows={2} /></Field>
              </div>
              <label className="fcheck"><input type="checkbox" checked={!!get(d, `${p}.base`)} onChange={(e) => set(`${p}.base`, e.target.checked)} /> Core check: must hold for the control to count at all</label>
            </>}
          </Repeat>
        </section>
        <section><h2>Looks done, isn't</h2>
          <Field c={c} path="formal_implementation_risk" label="The usual failure" entity="mitigation" name="formal_implementation_risk" optional><Area c={c} path="formal_implementation_risk" rows={3} ph="What a useless implementation that looks like this control looks like" /></Field>
          <Field c={c} path="anti_patterns" label="Anti-patterns" entity="mitigation" name="anti_patterns" optional><Lines c={c} path="anti_patterns" add="Add an anti-pattern" /></Field>
        </section>
        <section><h2>Where it sits and when it breaks</h2>
          {decision("locus", "Layer", enumOf(schema, "locus", "value").map((k) => [k, k === "split" ? "Split" : k === "product" ? "Product" : "Infrastructure"]))}
          {decision("failure_behavior", "When it breaks", enumOf(schema, "failure_behavior", "value").map((k) => [k, k === "fail_closed" ? "Fails closed" : k === "fail_open" ? "Fails open" : "Degrades"]))}
          <Field c={c} path="control_mechanism" label="How it works" entity="mitigation" name="control_mechanism" optional><Area c={c} path="control_mechanism" rows={6} ph="Markdown: paragraphs, lists, tables" /></Field>
          <Field c={c} path="requires" label="Presupposes" entity="mitigation" name="requires" optional>
            <div className="chips">{(d.requires || []).map((r: string) => <span className="chip" key={r}>{nameOf[r] || r}<button type="button" aria-label={`Remove ${r}`} onClick={() => set("requires", d.requires.filter((x: string) => x !== r))}>×</button></span>)}</div>
            <Pick id="req-pick" options={otherCtrls} exclude={new Set(d.requires || [])} ph="+ Add a control it needs in place" onPick={(r) => set("requires", [...(d.requires || []), r])} />
          </Field>
        </section>
        <section><h2>What it records · {(d.telemetry?.events || []).length}</h2>
          <Repeat c={c} path="telemetry.events" add="Add an event" blank={() => ({ name: "", records: "", attributes: "" })} head={(x, i) => x.name || `Event ${i + 1}`}>
            {(p) => <>
              <div className="frow">
                <Field c={c} path={`${p}.name`} label="Event name"><Text c={c} path={`${p}.name`} mono /></Field>
                <Field c={c} path={`${p}.attributes`} label="Attributes"><Text c={c} path={`${p}.attributes`} mono ph="actor, target, decision" /></Field>
              </div>
              <Field c={c} path={`${p}.records`} label="What it establishes"><Text c={c} path={`${p}.records`} /></Field>
            </>}
          </Repeat>
          <Field c={c} path="telemetry.evidence" label="What the events prove together" optional><Area c={c} path="telemetry.evidence" rows={2} /></Field>
        </section>
        <section><h2>Questions · {(d.faq || []).length}</h2>
          <Repeat c={c} path="faq" add="Add a question" blank={() => ({ question: "", answer: "" })} head={(x, i) => x.question || `Question ${i + 1}`}>
            {(p) => <>
              <Field c={c} path={`${p}.question`} label="Question"><Text c={c} path={`${p}.question`} /></Field>
              <Field c={c} path={`${p}.answer`} label="Answer"><Area c={c} path={`${p}.answer`} rows={3} /></Field>
            </>}
          </Repeat>
        </section>
        <section><h2>How it is put in place · {(d.implementations || []).length}</h2>
          <p className="sub">Empty in the reference library. An organisation records here how it runs this control.</p>
          <Repeat c={c} path="implementations" add="Add an implementation" blank={() => ({ title: "", description: "", reference: "", coverage: "local", covers: "", owner: "" })} head={(x, i) => x.title || `Implementation ${i + 1}`}>
            {(p) => <>
              <Field c={c} path={`${p}.title`} label="Title" entity="implementation" name="title"><Text c={c} path={`${p}.title`} /></Field>
              <Field c={c} path={`${p}.description`} label="Description" entity="implementation" name="description"><Area c={c} path={`${p}.description`} rows={3} /></Field>
              <div className="frow">
                <Field c={c} path={`${p}.coverage`} label="Coverage" entity="implementation" name="coverage"><Seg c={c} path={`${p}.coverage`} opts={enumOf(schema, "implementations", "coverage").map((k) => [k, cap(k)])} /></Field>
                <Field c={c} path={`${p}.owner`} label="Owner" entity="implementation" name="owner" optional><Text c={c} path={`${p}.owner`} /></Field>
              </div>
              <Field c={c} path={`${p}.covers`} label="Boundary it covers" entity="implementation" name="covers" optional><Text c={c} path={`${p}.covers`} ph="Required when coverage is shared" /></Field>
              <Field c={c} path={`${p}.reference`} label="Link" entity="implementation" name="reference" optional><Text c={c} path={`${p}.reference`} mono ph="https://" /></Field>
            </>}
          </Repeat>
        </section>
        <section><h2>Upkeep</h2>
          <div className="frow">
            <Field c={c} path="maintainer" label="Maintainer" entity="mitigation" name="maintainer" optional><Text c={c} path="maintainer" /></Field>
            <Field c={c} path="review" label="When to review it" entity="mitigation" name="review" optional><Text c={c} path="review" /></Field>
          </div>
          <Field c={c} path="positioning" label="How it sits against tracked sources" entity="mitigation" name="positioning" optional><Area c={c} path="positioning" rows={3} /></Field>
        </section>
        {!isNew && <ClosesEditor ctrl={init!} threats={threats} />}
      </form>
      <SaveBar dirty={dirty} busy={busy} problems={0} error={err} what="control" onSave={save} leaving={guard.blocker}
        onCancel={() => nav(isNew ? "/controls" : `/controls/${init!.id}`)} onDelete={isNew ? undefined : del} />
    </Shell>
  );
}

/** Threats this control closes. A link lives on the threat, so it is written there at once. */
function ClosesEditor({ ctrl, threats }: { ctrl: Mitigation; threats: Threat[] }) {
  const [list, setList] = useState(threats);
  const [pending, setPending] = useState<{ tid: string; strength: string; rationale: string } | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const closes = list.flatMap((t) => t.mitigations.filter((l) => l.id === ctrl.id).map((l) => ({ t, l })));
  const linked = new Set(closes.map(({ t }) => t.id));
  const opts = [...list].sort((a, b) => a.title.localeCompare(b.title)).map((t) => ({ id: t.id, label: `${t.title} · ${t.id}` }));
  const reload = async () => { forget("/threats"); const r = await fetch(`/api${THREATS}`).then((x) => x.json()); setList(r.threats); };
  async function link() {
    if (!pending) return;
    try { await send("PUT", `/threats/${pending.tid}/mitigations/${ctrl.id}`, { strength: pending.strength, rationale: pending.rationale }); setPending(null); setErr(null); await reload(); }
    catch (e) { setErr((e as Error).message); }
  }
  async function unlink(tid: string) {
    try { await send("DELETE", `/threats/${tid}/mitigations/${ctrl.id}`); await reload(); } catch (e) { setErr((e as Error).message); }
  }
  return <section><h2>Closes · {closes.length}</h2>
    <p className="sub">Links are stored on each threat and saved the moment you add or remove one.</p>
    {err && <p className="ferr" role="alert">{err}</p>}
    <table className="tbl"><tbody>{closes.map(({ t, l }) => <tr key={t.id}>
      <td><Link className="rlink" to={`/threats/${t.id}`}>{t.title}</Link><div className="t3 small">{l.strength === "gating" ? "Stops it" : "Reduces it"} · {harmLabel(t.harm)}</div></td>
      <td className="t2 small">{l.rationale}</td>
      <td className="n"><Link className="small" to={`/threats/${t.id}/edit`}>Edit link</Link> <button type="button" className="fdel" aria-label={`Unlink ${t.title}`} title="Unlink" onClick={() => unlink(t.id)}>×</button></td>
    </tr>)}</tbody></table>
    {pending ? <div className="fcard" style={{ marginTop: 12 }}>
      <div className="fcard-h"><span>{list.find((t) => t.id === pending.tid)?.title}</span><button type="button" className="fdel" aria-label="Cancel" onClick={() => setPending(null)}>×</button></div>
      <div className="fld"><span className="fl">Role</span><div className="toggle fseg">{([["gating", "Stops it"], ["soft", "Reduces it"]] as const).map(([k, l]) => <button type="button" key={k} aria-pressed={pending.strength === k} onClick={() => setPending({ ...pending, strength: k })}>{l}</button>)}</div></div>
      <div className="fld"><label className="fl" htmlFor="new-rat">Why it answers this threat</label><textarea id="new-rat" className="fi" rows={2} value={pending.rationale} onChange={(e) => setPending({ ...pending, rationale: e.target.value })} /></div>
      <button type="button" className="btn solid" disabled={!pending.rationale.trim()} onClick={link}>Link</button>
    </div> : <div style={{ marginTop: 12 }}><Pick id="thr-pick" options={opts} exclude={linked} ph="+ Link to a threat: type its title" onPick={(tid) => setPending({ tid, strength: "gating", rationale: "" })} /></div>}
  </section>;
}
