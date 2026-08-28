const { ScreenTabs, SearchInput, FacetPanel, RailRow, IconButton, Button, Badge, EmptyState, Toast, SavedDialog } = window.KeelDesignSystem_7d5998;

const SCREENS = [["overview","Overview"],["threats","Threats"],["mitigations","Mitigations"],["style","Style guide"],["reports","Reports"]];

function RailHeader({ title, count, onNew, collapsed, onCollapse }) {
  return (
    <header style={{
      padding: collapsed ? "12px 0" : "15px 18px", borderBottom: "1px solid var(--line-panel)",
      display: "flex", alignItems: "center", gap: "8px",
      justifyContent: collapsed ? "center" : "flex-start",
    }}>
      <IconButton glyph={collapsed ? "»" : "«"} title={collapsed ? "Expand" : "Collapse"} onClick={onCollapse} />
      {collapsed ? null : <>
        <h1 style={{ fontSize: "var(--fs-15)", margin: 0, fontWeight: "var(--fw-bold)", letterSpacing: "var(--ls-title)" }}>{title}</h1>
        <span style={{ color: "var(--text-faint)", fontSize: "var(--fs-12)", marginLeft: "auto", fontVariantNumeric: "var(--numeric)" }}>{count}</span>
        {onNew ? <Button size="sm" glyph="＋" onClick={onNew} style={{ marginLeft: "8px" }}>New</Button> : null}
      </>}
    </header>
  );
}

/** The app frame: one CSS grid, full height, both side tracks user-driven. */
function AppShell({ screen, onScreen, rail, main, preview, previewTitle, toast, saved, onCloseSaved }) {
  const [collapsed, setCollapsed] = React.useState(false);
  const railW = collapsed ? "var(--rail-w-collapsed)" : "var(--rail-w)";
  const prevW = preview ? "var(--preview-w)" : "0px";
  return (
    <div style={{
      display: "grid", gridTemplateColumns: railW + " 1fr " + prevW,
      height: "100vh", background: "var(--surface-app)",
      font: "var(--fs-14)/var(--lh-base) var(--font-sans)", color: "var(--text-strong)",
    }}>
      <aside style={{
        background: "var(--surface-panel)", borderRight: "1px solid var(--line-panel)",
        display: "flex", flexDirection: "column", minHeight: 0, overflow: "hidden",
      }}>
        {collapsed ? null : <ScreenTabs screens={SCREENS} value={screen} onChange={onScreen} />}
        {rail({ collapsed, setCollapsed })}
      </aside>
      <main style={{ overflowY: "auto", padding: "var(--pad-main)", minWidth: 0 }}>{main}</main>
      {preview ? (
        <section style={{
          background: "var(--surface-panel)", borderLeft: "1px solid var(--line-panel)",
          overflowY: "auto", padding: "20px",
        }}>
          <p style={{
            fontSize: "var(--fs-11)", textTransform: "uppercase", letterSpacing: "var(--ls-eyebrow)",
            color: "var(--text-faint)", fontWeight: "var(--fw-bold)", margin: "0 0 12px",
          }}>{previewTitle || "Preview"}</p>
          {preview}
        </section>
      ) : null}
      <Toast message={toast ? toast.message : ""} tone={toast && toast.tone} show={Boolean(toast)} />
      <SavedDialog show={Boolean(saved)} file={saved && saved.file} onClose={onCloseSaved} repoUrl="https://github.com/roselis-lab/keel" />
    </div>
  );
}

function Prose({ children, read }) {
  return <p style={{
    margin: 0, whiteSpace: "pre-wrap", fontSize: "var(--fs-14)",
    lineHeight: "var(--lh-prose)", color: read ? "var(--text-body-read)" : "var(--text-body)",
  }}>{children}</p>;
}

function PanelCard({ label, children, style }) {
  return (
    <div style={{
      background: "var(--surface-panel)", border: "1px solid var(--line-panel)",
      borderRadius: "var(--r-10)", padding: "var(--pad-section)", ...style,
    }}>
      <h3 style={{
        fontSize: "var(--fs-11)", textTransform: "uppercase", letterSpacing: "var(--ls-eyebrow)",
        color: "var(--navy-700)", margin: "0 0 9px", fontWeight: "var(--fw-bold)",
      }}>{label}</h3>
      {children}
    </div>
  );
}

Object.assign(window, { AppShell, RailHeader, Prose, PanelCard, SCREENS });
