const { RailRow, SearchInput, FacetPanel, SectionBand, Card, EditorCard, EntityHeader, Breadcrumb,
  Button, Badge, Field, TextInput, TextArea, Select, CheckSet, GapChips, DiffView, ErrorSummary, WarnBanner, EmptyState } = window.KeelDesignSystem_7d5998;

const PATCH = `@@ -18,7 +18,9 @@ weaknesses:
   nature: targeted
-reachability: NOT applicable if the tool is read-only.
+reachability: NOT applicable if the reachable tools have no operations with real
+  consequences (read-only, no side effects), or the model influences neither the
+  choice of tool nor its arguments (a rigidly predefined pipeline).
 mitigations:
 - id: CTRL-TOOL-ALLOWLIST`;

function ThreatsRail({ data, sel, onSelect, q, setQ, facets, setFacets, open, setOpen, collapsed, setCollapsed, onNew }) {
  const E = data.enums;
  const active = Object.values(facets).reduce((n, a) => n + a.length, 0);
  const items = data.threats.filter(t => {
    const hay = [t.id, t.title, t.reachability, ...t.weaknesses.map(w => w.text)].join(" ").toLowerCase();
    if (q && !hay.includes(q.toLowerCase())) return false;
    for (const [k, vals] of Object.entries(facets)) {
      if (!vals.length) continue;
      const mine = k === "harm" ? [t.harm] : k === "component" ? t.weaknesses.map(w => w.component)
        : k === "mitigation" ? (t.mitigations.length ? (t.mitigations.some(m => m.strength === "gating") ? ["gating"] : ["soft"]) : ["none"])
        : t[k] || [];
      if (!mine.some(v => vals.includes(v))) return false;
    }
    return true;
  });
  return (
    <>
      <RailHeader title="Keel · Threats" count={items.length + " / " + data.threats.length}
        onNew={onNew} collapsed={collapsed} onCollapse={() => setCollapsed(c => !c)} />
      {collapsed ? null : <>
        <SearchInput placeholder="Filter threats…" value={q} onChange={e => setQ(e.target.value)} />
        <FacetPanel open={open} onOpen={setOpen} activeCount={active} selected={facets}
          onClear={() => setFacets({ harm: [], surface: [], source: [], component: [], mitigation: [] })}
          onToggle={(k, v) => setFacets(f => ({ ...f, [k]: f[k].includes(v) ? f[k].filter(x => x !== v) : [...f[k], v] }))}
          groups={[
            { key: "harm", label: "Harm", options: E.harm },
            { key: "surface", label: "Surface", options: E.surface },
            { key: "source", label: "Source", options: E.source },
            { key: "component", label: "Weakness component", options: E.component },
            { key: "mitigation", label: "Mitigation strength", options: [["gating","has a gating control"],["soft","soft only"],["none","none linked"]] },
          ]} />
        <div style={{ overflowY: "auto", flex: 1, minHeight: 0 }}>
          {items.length ? items.map(t => (
            <RailRow key={t.id} id={t.id} title={t.title} selected={sel === t.id} onClick={() => onSelect(t.id)}
              badges={<>
                <Badge tone="type" mono>{t.harm}</Badge>
                {t.mitigations.length ? null : <Badge tone="advice">no mitigation</Badge>}
                {t.weaknesses.length ? null : <Badge tone="advice">no weakness</Badge>}
              </>} />
          )) : <EmptyState top="40px">No matches.</EmptyState>}
        </div>
      </>}
    </>
  );
}

function ThreatRead({ t, mitById, onEdit, onDelete, onJump, onGap, showDiff, setShowDiff }) {
  const gaps = [];
  if (!t.reachability) gaps.push("reachability");
  if (!t.references.length) gaps.push("references");
  if (!t.tags.length) gaps.push("tags");
  if (!t.weaknesses.length) gaps.push("weaknesses");
  if (!t.mitigations.length) gaps.push("mitigations");
  const gating = t.mitigations.filter(m => m.strength === "gating").length;
  return (
    <div>
      <Breadcrumb type="Threats" id={t.id} lastChanged={t.lastChanged} onViewChange={() => setShowDiff(d => !d)} />
      {showDiff ? <DiffView file={"catalog/threats/" + t.id + ".yaml"} patch={PATCH} style={{ marginBottom: "14px" }} /> : null}
      <EntityHeader glyph="T" title={t.title} id={t.id}
        badges={<>
          <Badge tone="type" mono>{t.harm}</Badge>
          {t.surface.map(s => <Badge key={s} tone="soft">{s}</Badge>)}
          {t.source.map(s => <Badge key={s} tone="soft">{s}</Badge>)}
          {t.tags.map(s => <Badge key={s} tone="ok">{s}</Badge>)}
        </>}
        actions={<><Button size="sm" onClick={onDelete}>Delete</Button><Button variant="primary" size="sm" onClick={onEdit}>Edit</Button></>} />

      {t.mitigations.length && !gating ? (
        <WarnBanner style={{ marginTop: "16px" }}>Every mitigation on this threat is soft — nothing gates it.</WarnBanner>
      ) : null}

      {t.weaknesses.length ? (
        <SectionBand label="Weaknesses" sub="the predisposing conditions it rests on" count={t.weaknesses.length}>
          {t.weaknesses.map((w, i) => (
            <Card key={i} id={w.component} badges={<Badge tone={w.nature === "targeted" ? "type" : "soft"}>{w.nature}</Badge>} desc={w.text}
              style={i === t.weaknesses.length - 1 ? { marginBottom: 0 } : null} />
          ))}
        </SectionBand>
      ) : null}

      {t.reachability ? (
        <SectionBand label="Reachability" sub="when it is NOT a live path, judged un-mitigated">
          <Prose read>{t.reachability}</Prose>
        </SectionBand>
      ) : null}

      {t.mitigations.length ? (
        <SectionBand label="Mitigations" count={gating + " gating · " + (t.mitigations.length - gating) + " soft"}>
          {t.mitigations.map((m, i) => {
            const card = mitById[m.id];
            return <Card key={m.id} id={m.id} title={card ? card.name : "— card not found —"} jump onClick={() => onJump(m.id)}
              badges={<>
                <Badge tone={m.strength === "gating" ? "harm" : "soft"}>{m.strength}</Badge>
                {card ? null : <Badge tone="danger">dangling</Badge>}
              </>}
              rationale={m.rationale} style={i === t.mitigations.length - 1 ? { marginBottom: 0 } : null} />;
          })}
        </SectionBand>
      ) : null}

      {t.references.length ? (
        <SectionBand label="References">
          {t.references.map(r => <Card key={r.id} id={r.id} desc={r.url} style={{ marginBottom: 0 }} />)}
        </SectionBand>
      ) : null}

      {gaps.length ? <GapChips items={gaps} onPick={onGap} /> : (
        <p style={{ color: "var(--text-faint)", fontSize: "var(--fs-12)", fontStyle: "italic", margin: "16px 0 0" }}>
          Every field on this threat is authored.
        </p>
      )}
    </div>
  );
}

function ThreatEdit({ t, enums, focusField, onCancel, onSave }) {
  const [draft, setDraft] = React.useState(t);
  const [openCards, setOpenCards] = React.useState([0]);
  React.useEffect(() => setDraft(t), [t.id]);
  const set = (k, v) => setDraft(d => ({ ...d, [k]: v }));
  const errors = draft.title.trim() ? [] : ["title: a threat must have a title"];
  const advice = [];
  if (!draft.weaknesses.length) advice.push("weaknesses: a threat should rest on at least one architectural condition");
  if (draft.mitigations.length && !draft.mitigations.some(m => m.strength === "gating"))
    advice.push("mitigations: every link is soft — nothing gates this threat");
  if (!draft.reachability) advice.push("reachability: no carve-out authored, so every deployment inherits this threat");
  return (
    <div>
      <EntityHeader glyph="T" title="Editing" id={draft.id}
        actions={<><Button size="sm" onClick={onCancel}>Cancel</Button>
          <Button variant="primary" size="sm" disabled={errors.length > 0} onClick={() => onSave(draft)}>Save</Button></>} />
      {errors.length ? <ErrorSummary title={errors.length + " problems block this save"} items={errors} /> : null}
      {advice.length ? <ErrorSummary tone="advice" title={advice.length + " things worth a look"} items={advice} /> : null}

      <SectionBand as="fieldset" label="Identity">
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--field-gap)" }}>
          <Field label="Title" hint="One line: the action plus its consequence." error={errors.length ? "Required." : null}>
            <TextInput title value={draft.title} invalid={errors.length > 0} autoFocus={focusField === "title"}
              onChange={e => set("title", e.target.value)} />
          </Field>
          <Field label="Harm" hint="The consequence class if it fires.">
            <Select value={draft.harm} options={enums.harm} onChange={e => set("harm", e.target.value)} />
          </Field>
          <Field label="Surface" hint="Which trust boundary untrusted influence crosses.">
            <CheckSet options={enums.surface} value={draft.surface}
              onToggle={v => set("surface", draft.surface.includes(v) ? draft.surface.filter(x => x !== v) : [...draft.surface, v])} />
          </Field>
          <Field label="Source" hint="Who or what drives it.">
            <CheckSet options={enums.source} value={draft.source}
              onToggle={v => set("source", draft.source.includes(v) ? draft.source.filter(x => x !== v) : [...draft.source, v])} />
          </Field>
        </div>
      </SectionBand>

      <SectionBand as="fieldset" label="Weaknesses" count={draft.weaknesses.length}>
        {draft.weaknesses.map((w, i) => (
          <EditorCard key={i} summary={w.component + " · " + w.nature} open={openCards.includes(i)}
            onToggle={() => setOpenCards(o => o.includes(i) ? o.filter(x => x !== i) : [...o, i])}
            onRemove={() => set("weaknesses", draft.weaknesses.filter((_, j) => j !== i))}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--field-gap)" }}>
              <Field label="Component" hint="Which owned part it sits on.">
                <Select value={w.component} options={enums.component}
                  onChange={e => set("weaknesses", draft.weaknesses.map((x, j) => j === i ? { ...x, component: e.target.value } : x))} />
              </Field>
              <Field label="Nature" hint="targeted exploits it; secondary only amplifies.">
                <Select value={w.nature} options={enums.nature}
                  onChange={e => set("weaknesses", draft.weaknesses.map((x, j) => j === i ? { ...x, nature: e.target.value } : x))} />
              </Field>
            </div>
            <Field label="Text" hint="Cause + where + defect — an architectural condition, not a narrative."
              guidance="State the condition that predisposes the system. Do not describe an attacker's steps, and do not name a control."
              style={{ marginTop: "var(--field-gap)" }}>
              <TextArea rows={3} value={w.text}
                onChange={e => set("weaknesses", draft.weaknesses.map((x, j) => j === i ? { ...x, text: e.target.value } : x))} />
            </Field>
          </EditorCard>
        ))}
        <Button size="sm" glyph="＋" onClick={() => set("weaknesses", [...draft.weaknesses, { component: "tool", nature: "targeted", text: "" }])}>Add weakness</Button>
      </SectionBand>

      <SectionBand as="fieldset" label="Reachability" sub="the rule-out gate">
        <Field label="" hint="Open with “NOT applicable if”. Judge on the un-mitigated architecture." reserveHint
          advice={draft.reachability ? null : "No carve-out authored yet."}
          guidance="Describe the architecture that removes the path — never a control that mitigates it. Two carve-outs at most.">
          <TextArea rows={3} value={draft.reachability} autoFocus={focusField === "reachability"}
            onChange={e => set("reachability", e.target.value)} placeholder="NOT applicable if…" />
        </Field>
      </SectionBand>
    </div>
  );
}
Object.assign(window, { ThreatsRail, ThreatRead, ThreatEdit });
