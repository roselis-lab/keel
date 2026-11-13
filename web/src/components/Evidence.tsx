import { createContext, useContext, useEffect, useId, useLayoutEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { useNavigate } from "react-router";
import { clipQuote, splitMarks, whereLines } from "../lib/evidence";
import type { Evidence, Report } from "../lib/types";

/* A report's prose points at its evidence with `[3]` or `#ev-3`. Inside <EvidenceRefs>
   such a mark is a link: a click goes to the evidence, a hover or focus shows its quote,
   path:lines, repository and short commit. A mark on evidence the report does not hold
   stays text, struck out. Outside a report the text renders as it always did. */

type Refs = { byId: Map<number, Evidence>; base: string };
const Ctx = createContext<Refs | null>(null);

export function EvidenceRefs({ report, children }: { report: Report; children: ReactNode }) {
  const refs = useMemo(() => ({
    byId: new Map((report.evidence || []).map((e) => [e.id, e] as const)),
    base: `/reports/${report.system_id}/${report.date}`,
  }), [report]);
  return <Ctx.Provider value={refs}>{children}</Ctx.Provider>;
}

/** Text from a report, its evidence marks drawn as links. `still` is for text inside a
    button or a summary, where a link cannot sit: the mark keeps its tooltip, the click
    stays the button's. */
export function Ev({ text, still }: { text?: string | null; still?: boolean }) {
  const refs = useContext(Ctx);
  const s = String(text ?? "");
  const segs = refs ? splitMarks(s, refs.byId) : [];
  if (!refs || !segs.some((x) => x.id !== undefined)) return <>{s}</>;
  return <>{segs.map((x, i) => x.id === undefined ? x.text
    : x.broken ? <span key={i} className="evref broken" title={`There is no evidence ${x.id} in this report`}>{x.label}</span>
    : <Mark key={i} id={x.id} label={x.label} e={refs.byId.get(x.id)!} href={`${refs.base}#ev-${x.id}`} still={still} />)}</>;
}

/** Open the folds around evidence `id` on this page, scroll to it and outline it for a
    moment. False when the page does not show it. */
export function revealEvidence(id: number | string): boolean {
  const el = document.getElementById(`ev-${id}`);
  if (!el) return false;
  for (let d = el.closest("details"); d; d = d.parentElement?.closest("details") ?? null) d.open = true;
  const still = matchMedia("(prefers-reduced-motion: reduce)").matches;
  el.scrollIntoView({ behavior: still ? "auto" : "smooth", block: "center" });
  if (!el.hasAttribute("tabindex")) el.setAttribute("tabindex", "-1");
  el.focus({ preventScroll: true });
  el.classList.remove("evhit");
  void el.offsetWidth; // restart the outline when the same evidence is opened again
  el.classList.add("evhit");
  setTimeout(() => el.classList.remove("evhit"), 2400);
  return true;
}

function Mark({ id, label, e, href, still }: { id: number; label: string; e: Evidence; href: string; still?: boolean }) {
  const navigate = useNavigate();
  const tipId = useId();
  const [el, setEl] = useState<HTMLElement | null>(null);
  const [open, setOpen] = useState(false);
  useEffect(() => {
    if (!open) return;
    const close = () => setOpen(false);
    addEventListener("scroll", close, { passive: true, capture: true });
    return () => removeEventListener("scroll", close, { capture: true });
  }, [open]);
  const common = {
    className: "evref",
    "aria-describedby": open ? tipId : undefined,
    onMouseEnter: () => setOpen(true), onMouseLeave: () => setOpen(false),
    onFocus: () => setOpen(true), onBlur: () => setOpen(false),
    onKeyDown: (k: React.KeyboardEvent) => { if (k.key === "Escape") setOpen(false); },
  };
  const tip = open && el && createPortal(<Tip id={tipId} n={id} e={e} anchor={el} />, document.body);
  if (still) return <span ref={setEl} {...common}>{label}{tip}</span>;
  return <a ref={setEl} {...common} href={href} onClick={(c) => {
    if (c.button !== 0 || c.metaKey || c.ctrlKey || c.shiftKey || c.altKey) return;
    c.preventDefault();
    setOpen(false);
    if (!revealEvidence(id)) navigate(href);
  }}>{label}{tip}</a>;
}

function Tip({ id, n, e, anchor }: { id: string; n: number; e: Evidence; anchor: HTMLElement }) {
  const ref = useRef<HTMLDivElement>(null);
  const [pos, setPos] = useState<{ top: number; left: number } | null>(null);
  useLayoutEffect(() => {
    const t = ref.current!, r = anchor.getBoundingClientRect();
    const w = t.offsetWidth, h = t.offsetHeight, gap = 6, edge = 8;
    const below = r.bottom + gap + h <= innerHeight - edge || r.top - gap - h < edge;
    setPos({ top: below ? r.bottom + gap : r.top - gap - h, left: Math.max(edge, Math.min(r.left, innerWidth - edge - w)) });
  }, [anchor]);
  return (
    <div ref={ref} id={id} role="tooltip" className="evtip" style={pos || { top: 0, left: 0, visibility: "hidden" }}>
      <div className="evtip-h">Evidence {n}</div>
      <div className="evtip-q">{clipQuote(e.quote)}</div>
      {whereLines(e).map((l, i) => <div key={i} className="evtip-m">{l}</div>)}
    </div>
  );
}
