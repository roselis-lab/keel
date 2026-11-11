import type { MouseEvent } from "react";
import { useNavigate } from "react-router";
import { useApi } from "../lib/api";

type Drawn = { html: string | null; reason: string | null; note?: string | null };

/** The report's system as Archify draws it, from the report itself: who starts each
    risk, the parts of the system, its trust boundary and the part each risk sits on.
    Two shapes come back, three columns and one, and the section's own width picks one
    (styles.css, .dgm), so labels never shrink below a readable size. The figure is CSS
    only: hover, a tap that pins a box's card and the legend work without a script.
    An installed extension may draw it instead and say one line about it in `note`. */
export function SystemDiagram({ system, date }: { system: string; date: string }) {
  const base = `/reports/${system}/${date}/diagram`;
  const q = useApi<[Drawn, Drawn]>(`${base}?shape=wide`, `${base}?shape=narrow`);
  const nav = useNavigate();
  if (q.loading) return <div className="skeleton" style={{ height: 220, maxWidth: 700 }} />;
  if (q.error) return <p className="t2">The diagram did not load: {q.error.message}</p>;
  const [wide, narrow] = q.data;
  if (!wide.html || !narrow.html) return <p className="t2">{wide.reason || narrow.reason}</p>;
  const note = wide.note || narrow.note;
  // Links in the cards are app paths; follow them inside the app instead of reloading it.
  const follow = (e: MouseEvent) => {
    const href = (e.target as Element).closest("a")?.getAttribute("href");
    if (!href?.startsWith("/") || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey) return;
    e.preventDefault();
    nav(href);
  };
  return (
    <>
      {note && <p className="t2">{note}</p>}
      <div className="dgm" onClick={follow}>
        <div className="wide" dangerouslySetInnerHTML={{ __html: wide.html }} />
        <div className="narrow" dangerouslySetInnerHTML={{ __html: narrow.html }} />
      </div>
    </>
  );
}
