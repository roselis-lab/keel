import React from "react";

/** After a write: names the file to commit. Green left accent, dismissible, stays put. */
export function SavedDialog({ file, message = "Written to disk.", show = true, repoUrl, onClose, style }) {
  if (!show) return null;
  return (
    <div style={{
      position: "fixed", bottom: "20px", right: "22px", maxWidth: "340px",
      background: "#fff", border: "1px solid var(--border)", borderLeft: "4px solid var(--green)",
      color: "var(--navy-800)", padding: "13px 16px", borderRadius: "var(--r-10)",
      fontFamily: "var(--font-sans)", fontSize: "var(--fs-13)", lineHeight: 1.5,
      boxShadow: "var(--shadow-dialog)", zIndex: 60, ...style,
    }}>
      <div>{message}{" "}
        {file ? <code style={{ fontFamily: "var(--font-mono)", fontSize: "var(--fs-12)", color: "var(--navy-900)" }}>{file}</code> : null}
      </div>
      <div style={{ marginTop: "10px", display: "flex", gap: "12px", alignItems: "center" }}>
        {repoUrl ? <a href={repoUrl} style={{ color: "var(--crimson-600)", fontWeight: "var(--fw-semibold)", textDecoration: "none" }}>Open a pull request</a> : null}
        <button type="button" onClick={onClose} style={{
          marginLeft: "auto", border: "none", background: "none",
          color: "var(--navy-400)", fontSize: "var(--fs-12)", cursor: "pointer",
        }}>Dismiss</button>
      </div>
    </div>
  );
}
