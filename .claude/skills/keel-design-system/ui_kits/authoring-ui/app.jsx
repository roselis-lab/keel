const { EmptyState, Prose: _unused } = window.KeelDesignSystem_7d5998;
const DATA = window.KEEL_DATA;
const mitById = Object.fromEntries(DATA.mitigations.map(m => [m.id, m]));

function App() {
  const [screen, setScreen] = React.useState("overview");
  const [toast, setToast] = React.useState(null);
  const [saved, setSaved] = React.useState(null);

  // Threats
  const [tSel, setTSel] = React.useState("T-TOOL-ABUSE");
  const [tQ, setTQ] = React.useState("");
  const [tFacets, setTFacets] = React.useState({ harm: [], surface: [], source: [], component: [], mitigation: [] });
  const [tFacetsOpen, setTFacetsOpen] = React.useState(false);
  const [editing, setEditing] = React.useState(false);
  const [focusField, setFocusField] = React.useState(null);
  const [tDiff, setTDiff] = React.useState(false);
  const [threats, setThreats] = React.useState(DATA.threats);

  // Mitigations
  const [mSel, setMSel] = React.useState("CTRL-TOOL-ALLOWLIST");
  const [mQ, setMQ] = React.useState("");
  const [mFacets, setMFacets] = React.useState({ mitigation_class: [], status: [], implementations: [] });
  const [mFacetsOpen, setMFacetsOpen] = React.useState(false);
  const [mDiff, setMDiff] = React.useState(false);

  // Style guide
  const [sSel, setSSel] = React.useState("threat.reachability");
  const [sQ, setSQ] = React.useState("");
  const [sFacets, setSFacets] = React.useState({ entity: [], orphan: [] });
  const [sFacetsOpen, setSFacetsOpen] = React.useState(false);

  // Reports
  const [rSel, setRSel] = React.useState("checkout-agent");
  const [rQ, setRQ] = React.useState("");

  const flash = (message, tone) => { setToast({ message, tone }); setTimeout(() => setToast(null), 2200); };
  const data = { ...DATA, threats };
  const threat = threats.find(t => t.id === tSel);
  const mit = DATA.mitigations.find(m => m.id === mSel);
  const styleField = DATA.styleFields.find(f => f.entity + "." + f.field === sSel);

  const jumpToThreat = id => { const t = threats.find(x => x.id === id); if (t) { setTSel(id); setEditing(false); setTDiff(false); setScreen("threats"); } else flash("That threat is not in the catalog.", "error"); };
  const jumpToMit = id => { if (mitById[id]) { setMSel(id); setMDiff(false); setScreen("mitigations"); } else flash("That mitigation card no longer exists.", "error"); };

  const railFor = ({ collapsed, setCollapsed }) => {
    if (screen === "overview") return <>
      <RailHeader title="Keel · Overview" count="" collapsed={collapsed} onCollapse={() => setCollapsed(c => !c)} />
      {collapsed ? null : (
        <div style={{ padding: "16px 15px", color: "var(--navy-500)", fontSize: "var(--fs-13)", lineHeight: "var(--lh-legend)" }}>
          A snapshot of the library — counts, style-guide coverage, and soft gaps worth a look. Nothing here blocks a save.
        </div>
      )}
    </>;
    if (screen === "threats") return <ThreatsRail data={data} sel={tSel} onSelect={id => { setTSel(id); setEditing(false); setTDiff(false); }}
      q={tQ} setQ={setTQ} facets={tFacets} setFacets={setTFacets} open={tFacetsOpen} setOpen={setTFacetsOpen}
      collapsed={collapsed} setCollapsed={setCollapsed} onNew={() => flash("Draft threat created.")} />;
    if (screen === "mitigations") return <MitigationsRail data={data} sel={mSel} onSelect={id => { setMSel(id); setMDiff(false); }}
      q={mQ} setQ={setMQ} facets={mFacets} setFacets={setMFacets} open={mFacetsOpen} setOpen={setMFacetsOpen}
      collapsed={collapsed} setCollapsed={setCollapsed} onNew={() => flash("Draft mitigation card created.")} />;
    if (screen === "style") return <StyleRail data={data} sel={sSel} onSelect={setSSel}
      q={sQ} setQ={setSQ} facets={sFacets} setFacets={setSFacets} open={sFacetsOpen} setOpen={setSFacetsOpen}
      collapsed={collapsed} setCollapsed={setCollapsed} />;
    return <ReportsRail data={data} sel={rSel} onSelect={setRSel} q={rQ} setQ={setRQ}
      collapsed={collapsed} setCollapsed={setCollapsed} />;
  };

  let main = null;
  if (screen === "overview") main = <OverviewScreen data={data} onJump={id => id.startsWith("CTRL") ? jumpToMit(id) : jumpToThreat(id)} />;
  else if (screen === "threats") main = !threat ? <EmptyState>Select a threat from the list.</EmptyState>
    : editing
      ? <ThreatEdit t={threat} enums={DATA.enums} focusField={focusField}
          onCancel={() => { setEditing(false); setFocusField(null); }}
          onSave={d => { setThreats(ts => ts.map(x => x.id === d.id ? d : x)); setEditing(false); setFocusField(null);
            setSaved({ file: "catalog/threats/" + d.id + ".yaml" }); }} />
      : <ThreatRead t={threat} mitById={mitById} onJump={jumpToMit}
          onEdit={() => setEditing(true)} onDelete={() => flash("Delete needs a confirmation step.", "error")}
          onGap={f => { setFocusField(f); setEditing(true); }} showDiff={tDiff} setShowDiff={setTDiff} />;
  else if (screen === "mitigations") main = !mit ? <EmptyState>Select a mitigation card from the list.</EmptyState>
    : <MitigationRead m={mit} threats={threats} onJump={jumpToThreat}
        onEdit={() => flash("Mitigation editing lives on the same form as threats.")}
        onDelete={() => flash("Deleting a card unlinks it from every threat.", "error")}
        onGap={() => flash("Jumped to the first unauthored field.")}
        showDiff={mDiff} setShowDiff={setMDiff} />;
  else if (screen === "style") main = !styleField ? <EmptyState>Select a field from the tree.</EmptyState>
    : <StyleEditor field={styleField} onSave={f => setSaved({ file: "catalog/style_guide/" + f.entity + ".yaml" })} />;
  else main = <ReportScreen report={DATA.report} onJump={jumpToThreat} />;

  const preview = screen === "style" && styleField ? <StylePreview field={styleField} /> : null;

  return <AppShell screen={screen} onScreen={s => { setScreen(s); setEditing(false); }}
    rail={railFor} main={main} preview={preview} previewTitle="What the author sees"
    toast={toast} saved={saved} onCloseSaved={() => setSaved(null)} />;
}
ReactDOM.createRoot(document.getElementById("root")).render(<App />);
