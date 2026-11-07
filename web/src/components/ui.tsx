import { useEffect, useRef, type ReactNode } from "react";
import { Link, NavLink } from "react-router";
import type { Finding, Level } from "../lib/types";
import { backing, BACKING } from "../lib/report";
import { cap } from "../lib/text";

const SHAPE: Record<Level, ReactNode> = {
  high: <svg viewBox="0 0 12 12" aria-hidden="true"><path d="M6 0 12 6 6 12 0 6z" fill="currentColor" /></svg>,
  medium: <svg viewBox="0 0 12 12" aria-hidden="true"><path d="M6 1 11.5 11h-11z" fill="currentColor" /></svg>,
  low: <svg viewBox="0 0 12 12" aria-hidden="true"><circle cx="6" cy="6" r="4.5" fill="none" stroke="currentColor" strokeWidth="2" /></svg>,
};

/** Severity: a shape and a word, so it never rests on colour alone. */
export const Sev = ({ v, children }: { v: Level; children?: ReactNode }) =>
  <span className={`sev ${v}`}>{SHAPE[v]}{children ?? cap(v)}</span>;
export const Shape = ({ v, title }: { v: Level; title: string }) =>
  <span className={`sev ${v}`} title={title} aria-label={title}>{SHAPE[v]}</span>;
/** The solid hazard label: the one place a severity is a block of colour. Severity first, likelihood beside it, never merged. */
export const Grade = ({ f }: { f: { risk: { severity: Level; likelihood: Level } } }) => (
  <span className="gradev"><span className={`label ${f.risk.severity}`}>{f.risk.severity}</span><span className="lik">{f.risk.likelihood} likelihood</span></span>
);
export const Backing = ({ f }: { f: Finding }) => { const k = backing(f); return <span className={`back ${k}`}>{BACKING[k]}</span>; };

const NAV: [string, string][] = [["/", "Overview"], ["/reports", "Reports"], ["/compliance", "Compliance"], ["/threats", "Threats"], ["/controls", "Controls"], ["/coverage", "Coverage"]];

export function Shell({ title, rail, side, children }: { title: string; rail?: ReactNode; side?: ReactNode; children: ReactNode }) {
  useEffect(() => { document.title = title === "Overview" ? "Keel" : `${title} · Keel`; }, [title]);
  const nav = useRef<HTMLElement>(null);
  // On a phone the menu scrolls; keep the current section in view.
  useEffect(() => { const a = nav.current?.querySelector<HTMLElement>('[aria-current="page"]'); if (!a || !nav.current) return; const over = a.getBoundingClientRect().right - nav.current.getBoundingClientRect().right + 32; if (over > 0) nav.current.scrollLeft += over; }, [title]);
  return (
    <>
      <a className="visually-hidden" href="#main">Skip to content</a>
      <header className="top"><div className="top-in">
        <Link className="mark" to="/">Keel</Link>
        <nav className="nav" aria-label="Main" ref={nav}>
          {NAV.map(([to, n]) => <NavLink key={to} to={to} end={to === "/"}>{n}</NavLink>)}
        </nav>
      </div></header>
      <div className={`wrap r${rail ? 1 : 0} s${side ? 1 : 0}`}>
        {rail && <aside className="rail" aria-label="Pages in this section">{rail}</aside>}
        <main id="main">{children}</main>
        {side}
      </div>
    </>
  );
}

export function Head({ title, meta, lede, actions }: { title: ReactNode; meta?: ReactNode[]; lede?: ReactNode; actions?: ReactNode }) {
  return (
    <header className="hdr">
      <h1>{title}</h1>
      {meta && <div className="meta">{meta.filter(Boolean).map((m, i) => <span key={i}>{m}</span>)}</div>}
      {lede}
      {actions && <div className="actions">{actions}</div>}
    </header>
  );
}

export function Toggle<T extends string>({ value, options, onChange, label }: { value: T; options: [T, string][]; onChange: (v: T) => void; label: string }) {
  return (
    <div className="toggle" role="group" aria-label={label}>
      {options.map(([v, l]) => <button key={v} aria-pressed={value === v} onClick={() => onChange(v)}>{l}</button>)}
    </div>
  );
}

export const Loading = () => (
  <div aria-busy="true" aria-label="Loading"><div className="skeleton" style={{ height: 40, maxWidth: 420 }} /><div className="skeleton" /><div className="skeleton" style={{ maxWidth: 380 }} /></div>
);

export function Problem({ error, what }: { error: Error; what: string }) {
  const status = (error as { status?: number }).status;
  return (
    <div className="empty" role="alert">
      <b>{status === 404 ? `No ${what} here` : `Could not load ${what}`}</b>
      {status === 404 ? "The link may point to something that was renamed or removed." : `${error.message}. Is the Keel server running? Reload the page to try again.`}
      <p style={{ marginTop: 10 }}><Link to="/">Back to the overview</Link></p>
    </div>
  );
}

/** One stacked bar. Parts are named in a legend next to it, so the bar never stands alone. */
export function Stack({ parts, total, big, label }: { parts: [string, number][]; total: number; big?: boolean; label: string }) {
  return (
    <div className={`stack ${big ? "big" : ""}`} role="img" aria-label={label}>
      {parts.filter(([, n]) => n > 0).map(([k, n]) => <i key={k} className={`k-${k}`} style={{ width: `${(n / Math.max(total, 1)) * 100}%` }} />)}
    </div>
  );
}
export const Legend = ({ items }: { items: [string, string, number?][] }) => (
  <div className="legend">{items.map(([k, l, n]) => <span key={k}><i className={`k-${k}`} />{l}{n !== undefined ? ` · ${n}` : ""}</span>)}</div>
);
