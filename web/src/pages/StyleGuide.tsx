import { useEffect, useMemo, useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router";
import { forget, send, useApi, type SendError } from "../lib/api";
import { cap, firstSentence } from "../lib/text";
import { Head, Loading, Problem, Shell } from "../components/ui";
import { Area, type Ctx, type Draft, Field, type Guide, type GuideBar, Lines, SaveBar, setIn, useLeaveGuard } from "./Editor";
import { Saved } from "./Library";

/* The style guide: how each field of a library record should be written. The editors
   show a field's first sentence above it and the rest under "How to write it", with a
   link here. Each bar is edited on a page shaped like the other editors, with what an
   author will see shown live at the top. */

const ENTITY: Record<string, string> = { threat: "Threat", weakness: "Weak spot", mitigation_link: "Link from a threat to a control", mitigation: "Control", implementation: "How a control is put in place" };
const SLOTS = ["purpose", "content_requirements", "instructions", "avoid", "examples"] as const;
const filled = (b?: GuideBar | null) => SLOTS.filter((s) => { const x = b?.[s]; return Array.isArray(x) ? x.length > 0 : !!(x && String(x).trim()); }).length;
const human = (f: string) => cap(f.replace(/_/g, " "));
const entityName = (e: string) => ENTITY[e] || human(e);

export function StyleGuidePage() {
  const q = useApi<[Guide]>("/style-guide");
  // Back from an editor lands on the section it came from.
  const { hash } = useLocation();
  useEffect(() => { if (hash && !q.loading) document.getElementById(hash.slice(1))?.scrollIntoView({ block: "start" }); }, [hash, q.loading]);
  if (q.loading) return <Shell title="Style guide"><Loading /></Shell>;
  if (q.error) return <Shell title="Style guide"><Problem error={q.error} what="style guide" /></Shell>;
  const ents = Object.entries(q.data[0].entities);
  return (
    <Shell title="Style guide">
      <Saved />
      <Head title="Style guide" meta={[`${ents.reduce((n, [, e]) => n + Object.keys(e.fields).length, 0)} fields`, <Link key="t" to="/threats">Threats</Link>, <Link key="c" to="/controls">Controls</Link>]}
        lede={<p className="lede quiet list-lede">How each field of a threat or a control should be written. The editors show the first sentence of its purpose above the field, and the rest under “How to write it”.</p>} />
      {ents.map(([e, ent]) => <section key={e} id={e}><h2>{entityName(e)}</h2>
        <table className="tbl lib"><thead><tr><th>Field</th><th className="fit n">Written</th></tr></thead><tbody>
          {<tr><td><Link className="rlink" to={`/style-guide/${e}`}>The record as a whole</Link><div className="t2 small">{ent.entity?.purpose ? firstSentence(ent.entity.purpose) : "What one record is, and what to settle before writing any field."}</div></td>
            <td className="fit n m t2">{filled(ent.entity)} of 3</td></tr>}
          {Object.entries(ent.fields).map(([f, b]) => <tr key={f}>
            <td><Link className="rlink" to={`/style-guide/${e}/${f}`}>{human(f)}</Link> <span className="id">{f}</span>{b.is_orphan && <span className="t3 small"> · no longer in the schema</span>}
              <div className="t2 small">{b.purpose ? firstSentence(b.purpose) : <span className="t3">No purpose written yet.</span>}</div></td>
            <td className="fit n m t2">{filled(b)} of 5</td>
          </tr>)}
        </tbody></table></section>)}
    </Shell>
  );
}

export function StyleEditor() {
  const { entity = "", field } = useParams();
  const q = useApi<[Guide]>("/style-guide");
  if (q.loading) return <Shell title="Edit guidance"><Loading /></Shell>;
  if (q.error) return <Shell title="Edit guidance"><Problem error={q.error} what="style guide" /></Shell>;
  const ent = q.data[0].entities[entity];
  const bar = field ? ent?.fields[field] : ent ? ent.entity || {} : undefined;
  if (!bar) return <Shell title="Edit guidance"><Problem error={Object.assign(new Error("not found"), { status: 404 })} what="guidance" /></Shell>;
  return <StyleForm key={`${entity}/${field || ""}`} entity={entity} field={field} bar={bar} />;
}

function StyleForm({ entity, field, bar }: { entity: string; field?: string; bar: GuideBar }) {
  const nav = useNavigate();
  const record = !field;
  const start = useMemo<Draft>(() => ({
    purpose: bar.purpose || "", content_requirements: [...(bar.content_requirements || [])], instructions: [...(bar.instructions || [])],
    avoid: [...(bar.avoid || [])], examples: [...(bar.examples || [])],
  }), [bar]);
  const [d, setD] = useState<Draft>(start);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const dirty = JSON.stringify(d) !== JSON.stringify(start);
  const guard = useLeaveGuard(dirty);
  const set = (p: string, v: unknown) => { setD((x) => setIn(x, p, v)); setErr(null); };
  const c: Ctx = { d, set, errs: {}, advice: {} };
  const name = record ? "The record as a whole" : human(field!);
  const lines = (k: string) => (d[k] as string[]).map((s) => s.trim()).filter(Boolean);
  // What the editor will show for this field, built from the draft as you type.
  const preview: Ctx = { d: {}, set: () => {}, errs: {}, advice: {}, preview: true,
    guide: { entities: { [entity]: { fields: { [field || "_"]: { purpose: d.purpose, content_requirements: lines("content_requirements"), avoid: lines("avoid") } } } } } };

  async function save() {
    setBusy(true); setErr(null);
    const all: Draft = record ? { purpose: d.purpose, instructions: lines("instructions"), avoid: lines("avoid") }
      : { purpose: d.purpose, content_requirements: lines("content_requirements"), instructions: lines("instructions"), avoid: lines("avoid"), examples: lines("examples") };
    // Only what changed goes out, so the YAML diff shows the edit and nothing else.
    const body = Object.fromEntries(Object.entries(all).filter(([k, v]) => JSON.stringify(v) !== JSON.stringify(start[k])));
    try {
      await send("PATCH", `/style-guide/${entity}${record ? "" : `/${field}`}`, body);
      forget("/style-guide"); guard.release();
      nav(`/style-guide#${entity}`, { state: { saved: `Saved to catalog/style_guide/${entity}.yaml.` } });
    } catch (e) { const se = e as SendError; setErr(se.message + (se.hint ? ` — ${se.hint}` : "")); setBusy(false); }
  }

  return (
    <Shell title={`${name} · ${entityName(entity)} guidance`}>
      <nav className="crumbs" aria-label="Breadcrumb"><Link to="/style-guide">Style guide</Link><span>/</span><Link to={`/style-guide#${entity}`}>{entityName(entity)}</Link><span>/</span><span aria-current="page">{record ? "The record" : field}</span></nav>
      <Head title={name} meta={[entityName(entity), record ? "read before writing any field" : <span className="id" key="f">{field}</span>, `catalog/style_guide/${entity}.yaml`]} />
      {err && <div className="call warn" role="alert"><b>Not saved</b>{err}</div>}
      <form className="form" onSubmit={(e) => { e.preventDefault(); save(); }}>
        <section id="preview"><h2>What the author sees</h2>
          {record
            ? <div className="fcard"><p className="prose">{d.purpose.trim() || <span className="t3">No purpose yet.</span>}</p>
                {lines("instructions").length > 0 && <><p className="fl">Settle first</p><ul>{lines("instructions").map((x, i) => <li key={i}>{x}</li>)}</ul></>}
                {lines("avoid").length > 0 && <><p className="fl">Avoid</p><ul>{lines("avoid").map((x, i) => <li key={i}>{x}</li>)}</ul></>}</div>
            : <div className="fcard"><Field c={preview} path="preview" label={human(field!)} entity={entity} name={field}>
                <input className="fi" disabled placeholder={`The author's ${human(field!).toLowerCase()} goes here`} /></Field></div>}
          <p className="sub">{record ? "Read once before a new record is written, and what a review checks the record against." : "Changes here show up in the threat and control editors once you save."}</p>
        </section>
        <section><h2>Purpose</h2>
          <Field c={c} path="purpose" label={record ? "What one record is" : "What this field is for"}><Area c={c} path="purpose" rows={3} />
            {!record && <p className="fh">The first sentence shows above the field in the editor.</p>}</Field>
        </section>
        {!record && <section><h2>Include · {d.content_requirements.length}</h2>
          <Field c={c} path="content_requirements" label="What a good value has"><Lines c={c} path="content_requirements" add="Add a requirement" /></Field></section>}
        <section><h2>{record ? "Settle first" : "Instructions"} · {d.instructions.length}</h2>
          <Field c={c} path="instructions" label={record ? "What to decide before writing any field" : "Steps for writing it"} optional><Lines c={c} path="instructions" add="Add a step" /></Field></section>
        <section><h2>Avoid · {d.avoid.length}</h2>
          <Field c={c} path="avoid" label={record ? "How a record as a whole goes wrong" : "Mistakes to name"} optional><Lines c={c} path="avoid" add="Add a mistake" /></Field></section>
        {!record && <section><h2>Examples · {d.examples.length}</h2>
          <Field c={c} path="examples" label="Good values, written out" optional><Lines c={c} path="examples" add="Add an example" /></Field></section>}
      </form>
      <SaveBar dirty={dirty} busy={busy} problems={0} error={err} what="guidance" onSave={save} leaving={guard.blocker} onCancel={() => nav(`/style-guide#${entity}`)} />
    </Shell>
  );
}
