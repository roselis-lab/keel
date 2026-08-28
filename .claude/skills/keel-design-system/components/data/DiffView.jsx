import React from "react";

/** A unified git diff in GitHub's colours, deliberately not Keel's — a reviewer reads it instantly. */
export function DiffView({ file, patch = "", loading, style }) {
  const rows = [];
  let oldNo = null, newNo = null;
  for (const line of patch.split("\n")) {
    if (/^(diff |index |--- |\+\+\+ )/.test(line)) continue;
    const hunk = line.match(/^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@/);
    if (hunk) {
      oldNo = +hunk[1]; newNo = +hunk[2];
      rows.push({ kind: "hunk", text: line });
      continue;
    }
    if (line.startsWith("+")) rows.push({ kind: "add", text: line, n: newNo != null ? newNo++ : "" });
    else if (line.startsWith("-")) rows.push({ kind: "del", text: line, o: oldNo != null ? oldNo++ : "" });
    else rows.push({ kind: "ctx", text: line, o: oldNo != null ? oldNo++ : "", n: newNo != null ? newNo++ : "" });
  }
  const SKIN = {
    add: { bg: "var(--diff-add-bg)", gutter: "var(--diff-add-gutter)", gfg: "var(--diff-add-gutter-fg)", fg: "var(--diff-add-fg)", accent: "var(--green)" },
    del: { bg: "var(--diff-del-bg)", gutter: "var(--diff-del-gutter)", gfg: "var(--diff-del-gutter-fg)", fg: "var(--diff-del-fg)", accent: "var(--crimson-600)" },
    ctx: { bg: "transparent", gutter: "var(--tint)", gfg: "var(--navy-400)", fg: "var(--navy-700)" },
    hunk: { bg: "var(--diff-hunk-bg)", gutter: "var(--diff-hunk-bg)", gfg: "var(--navy-400)", fg: "var(--navy-500)" },
  };
  if (loading) {
    return <div style={{
      padding: "10px 12px", background: "#fff", border: "1px solid var(--border)",
      borderRadius: "var(--r-8)", fontFamily: "var(--font-mono)", fontSize: "var(--fs-12)",
      color: "var(--navy-400)", fontStyle: "italic", ...style,
    }}>Loading diff…</div>;
  }
  const gutter = (s, val, accent) => ({
    width: "1%", minWidth: "42px", textAlign: "right", padding: "0 10px",
    color: s.gfg, background: s.gutter, borderRight: "1px solid var(--border2)",
    userSelect: "none", whiteSpace: "nowrap", fontVariantNumeric: "var(--numeric)",
    borderLeft: accent ? "2px solid " + accent : "none",
  });
  return (
    <div style={{ border: "1px solid var(--border)", borderRadius: "var(--r-8)", overflow: "hidden", background: "#fff", ...style }}>
      {file ? <div style={{
        fontFamily: "var(--font-mono)", fontSize: "var(--fs-11)", color: "var(--navy-500)",
        padding: "6px 12px", background: "var(--tint)", borderBottom: "1px solid var(--border2)",
        whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis",
      }}>{file}</div> : null}
      <div style={{ overflowX: "auto" }}>
        <table style={{
          borderCollapse: "collapse", width: "100%", fontFamily: "var(--font-mono)",
          fontSize: "var(--fs-12)", lineHeight: 1.5,
        }}>
          <tbody>
            {rows.map((r, i) => {
              const s = SKIN[r.kind];
              if (r.kind === "hunk") {
                return <tr key={i} style={{ background: s.bg }}>
                  <td style={{ ...gutter(s), padding: "0 10px" }} />
                  <td style={{ ...gutter(s) }} />
                  <td style={{ padding: "0 10px", whiteSpace: "pre", color: s.fg }}>{r.text}</td>
                </tr>;
              }
              return (
                <tr key={i} style={{ background: s.bg }}>
                  <td style={gutter(s, r.o, s.accent)}>{r.o ?? ""}</td>
                  <td style={gutter(s)}>{r.n ?? ""}</td>
                  <td style={{ padding: "0 10px", whiteSpace: "pre", color: s.fg }}>{r.text}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
