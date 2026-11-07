import { useRef, useState } from "react";
import type { Report } from "../lib/types";
import { reportPath } from "../lib/report";

function Cmd({ text }: { text: string }) {
  const [done, setDone] = useState(false);
  return (
    <div className="cmd">
      <code>{text}</code>
      <button onClick={() => navigator.clipboard?.writeText(text).then(() => { setDone(true); setTimeout(() => setDone(false), 1600); })}>
        {done ? "Copied" : "Copy"}
      </button>
    </div>
  );
}

/** Save what is on screen as one file: the page's own styles inlined, every folded part
 *  opened, links made absolute. The same components render it, so it cannot drift. */
async function savePage(name: string) {
  const main = document.querySelector("main")?.cloneNode(true) as HTMLElement | null;
  if (!main) return;
  main.querySelectorAll("details").forEach((d) => d.setAttribute("open", ""));
  main.querySelectorAll(".risk").forEach((d) => d.classList.add("open"));
  main.querySelectorAll("[data-no-export], dialog").forEach((d) => d.remove());
  main.querySelectorAll("a[href]").forEach((a) => a.setAttribute("href", new URL(a.getAttribute("href")!, location.href).href));
  // The stylesheet as written, not re-serialised rules: the browser drops shorthands that use var().
  const links = Array.from(document.querySelectorAll<HTMLLinkElement>('link[rel="stylesheet"]'));
  let css = (await Promise.all(links.map((l) => fetch(l.href).then((r) => r.text(), () => "")))).join("\n");
  // Fonts load from this server while it is reachable; offline the page falls back to system type.
  css = css.replace(/url\((["']?)\//g, `url($1${location.origin}/`);
  const html = `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>${document.title}</title><style>${css}\n.wrap{display:block;max-width:1100px}</style></head><body><div class="wrap r0 s0">${main.outerHTML}</div></body></html>`;
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([html], { type: "text/html" }));
  a.download = name;
  a.click();
  URL.revokeObjectURL(a.href);
}

export function ShareButton({ r, fixes }: { r: Report; fixes: number }) {
  const ref = useRef<HTMLDialogElement>(null);
  const path = reportPath(r);
  return (
    <>
      <button className="btn solid" onClick={() => ref.current?.showModal()} data-no-export>
        <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 1v9M4.5 4.5 8 1l3.5 3.5M2 9v5h12V9" fill="none" stroke="currentColor" strokeWidth="1.6" /></svg>
        Share with the team
      </button>
      <dialog ref={ref} className="share" aria-labelledby="share-h" onClick={(e) => { if (e.target === ref.current) ref.current.close(); }}>
        <button className="close" onClick={() => ref.current?.close()}>Close</button>
        <h2 id="share-h">Share with the team</h2>
        <p className="t2">The team does not need Keel. Give them the page and the tickets in the tools they already use.</p>
        {r.status === "draft" && <p className="call warn" style={{ marginTop: 12 }}><b>This report is a draft</b>Mark it final before you share it. The commands below refuse a draft; to send it anyway, add <code>--allow-draft</code> yourself and tell whoever reads it.</p>}
        <ol>
          <li>
            <h3>One file to send</h3>
            <p className="t2">This report as a single page that opens in any browser, with nothing to install.</p>
            <p style={{ marginTop: 8 }}><button className="btn" onClick={() => savePage(`${r.system_id}-${r.date}.html`)}>Save as one page</button></p>
          </li>
          <li>
            <h3>A Confluence page and one Jira ticket per fix</h3>
            <p className="t2">A ticket for each of the {fixes} fixes still to build, each with what must hold, where and how to tell it is done. Write them to a folder first and read them:</p>
            <Cmd text={`keel export ${path} --out ${r.system_id}-export`} />
            <p className="t2" style={{ marginTop: 10 }}>Then send them. <code>--dry-run</code> shows what would go and sends nothing; drop it to publish. It reads <code>KEEL_CONFLUENCE_URL</code>, <code>KEEL_JIRA_URL</code>, <code>KEEL_ATLASSIAN_EMAIL</code> and <code>KEEL_ATLASSIAN_TOKEN</code> from the environment.</p>
            <Cmd text={`keel publish ${path} --confluence-space KEY --jira-project KEY --dry-run`} />
          </li>
          <li>
            <h3>A link</h3>
            <p className="t2">Opens for anyone who can reach this Keel server. If Keel runs on your own machine, that is only you: send the file instead.</p>
            <Cmd text={location.href} />
          </li>
        </ol>
      </dialog>
    </>
  );
}
