const { RailRow, SearchInput, FacetPanel, SectionBand, Card, EntityHeader, Breadcrumb, Button, Badge,
  GapChips, DiffView, EmptyState, WarnBanner } = window.KeelDesignSystem_7d5998;

const MIT_PATCH = `@@ -6,6 +6,8 @@ purpose: Restrict the agent to the smallest set of tools
 failure_behavior: 'Fail closed: an unlisted tool call is refused and logged.'
-implementations: []
+implementations:
+- name: Gateway tool policy
+  owner: Platform Security`;

function MitigationsRail({ data, sel, onSelect, q, setQ, facets, setFacets, open, setOpen, collapsed, setCollapsed, onNew }) {
  const E = data.enums;
  const active = Object.values(facets).reduce((n, a) => n + a.length, 0);
  const items = data.mitigations.filter(m => {
    if (q && ![m.id, m.name, m.purpose].join(" ").toLowerCase().includes(q.toLowerCase())) return false;
    if (facets.mitigation_class.length && !facets.mitigation_class.includes(m.mitigation_class)) return false;
    if (facets.status.length && !facets.status.includes(m.status)) return false;
    if (facets.implementations.length) {
      const v = m.implementations.length ? "recorded" : "empty";
      if (!facets.implementations.includes(v)) return false;
    }
    return true;
  });
  return (
    <>
      <RailHeader title="Keel · Mitigations" count={items.length + " / " + data.mitigations.length}
        onNew={onNew} collapsed={collapsed} onCollapse={() => setCollapsed(c => !c)} />
      {collapsed ? null : <>
        <SearchInput placeholder="Filter mitigations…" value={q} onChange={e => setQ(e.target.value)} />
        <FacetPanel open={open} onOpen={setOpen} activeCount={active} selected={facets}
          onClear={() => setFacets({ mitigation_class: [], status: [], implementations: [] })}
          onToggle={(k, v) => setFacets(f => ({ ...f, [k]: f[k].includes(v) ? f[k].filter(x => x !== v) : [...f[k], v] }))}
          groups={[
            { key: "mitigation_class", label: "Class", options: E.mitigation_class },
            { key: "status", label: "Status", options: E.status },
            { key: "implementations", label: "Implementations", options: [["recorded","recorded"],["empty","ships empty"]] },
          ]} />
        <div style={{ overflowY: "auto", flex: 1, minHeight: 0 }}>
          {items.length ? items.map(m => (
            <RailRow key={m.id} id={m.id} title={m.name} selected={sel === m.id} onClick={() => onSelect(m.id)}
              badges={<>
                <Badge tone="soft" mono>{m.mitigation_class}</Badge>
                <Badge tone={m.status === "verified" ? "ok" : "advice"}>{m.status}</Badge>
              </>} />
          )) : <EmptyState top="40px">No matches.</EmptyState>}
        </div>
      </>}
    </>
  );
}

function MitigationRead({ m, threats, onEdit, onDelete, onJump, onGap, showDiff, setShowDiff }) {
  const gaps = [];
  if (!m.implementations.length) gaps.push("implementations");
  if (!m.failure_behavior) gaps.push("failure_behavior");
  const linked = threats.filter(t => t.mitigations.some(l => l.id === m.id));
  return (
    <div>
      <Breadcrumb type="Mitigations" id={m.id} lastChanged="Last changed 6 days ago by jane" onViewChange={() => setShowDiff(d => !d)} />
      {showDiff ? <DiffView file={"catalog/mitigations/" + m.id + ".yaml"} patch={MIT_PATCH} style={{ marginBottom: "14px" }} /> : null}
      <EntityHeader glyph="C" title={m.name} id={m.id}
        badges={<>
          <Badge tone="type" mono>{m.mitigation_class}</Badge>
          <Badge tone={m.status === "verified" ? "ok" : "advice"}>{m.status}</Badge>
          <Badge tone="soft">{linked.length} threats addressed</Badge>
        </>}
        actions={<><Button size="sm" onClick={onDelete}>Delete</Button><Button variant="primary" size="sm" onClick={onEdit}>Edit</Button></>} />

      {m.mitigation_class === "detector" ? (
        <WarnBanner style={{ marginTop: "16px" }}>
          A detector fails open. It lowers likelihood and never closes the path — link it as soft.
        </WarnBanner>
      ) : null}

      <SectionBand label="Purpose"><Prose read>{m.purpose}</Prose></SectionBand>
      <SectionBand label="Scope"><Prose read>{m.scope}</Prose></SectionBand>
      <SectionBand label="Control mechanism"><Prose read>{m.control_mechanism}</Prose></SectionBand>
      {m.failure_behavior ? <SectionBand label="Failure behavior"><Prose read>{m.failure_behavior}</Prose></SectionBand> : null}

      {m.implementations.length ? (
        <SectionBand label="Implementations" sub="how this org realizes the control" count={m.implementations.length}>
          {m.implementations.map((im, i) => (
            <Card key={i} title={im.name} badges={<Badge tone="soft">{im.owner}</Badge>} desc={im.note}
              style={i === m.implementations.length - 1 ? { marginBottom: 0 } : null} />
          ))}
        </SectionBand>
      ) : null}

      <SectionBand label="Addresses" count={linked.length}>
        {linked.length ? linked.map((t, i) => {
          const link = t.mitigations.find(l => l.id === m.id);
          return <Card key={t.id} id={t.id} title={t.title} jump onClick={() => onJump(t.id)}
            badges={<Badge tone={link.strength === "gating" ? "harm" : "soft"}>{link.strength}</Badge>}
            rationale={link.rationale} style={i === linked.length - 1 ? { marginBottom: 0 } : null} />;
        }) : <Prose>Nothing links to this card yet.</Prose>}
      </SectionBand>

      {gaps.length ? <GapChips items={gaps} onPick={onGap} /> : null}
    </div>
  );
}
Object.assign(window, { MitigationsRail, MitigationRead });
