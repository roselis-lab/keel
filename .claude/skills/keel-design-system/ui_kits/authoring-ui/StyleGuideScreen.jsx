const { RailRow, SearchInput, FacetPanel, SectionBand, EntityHeader, Button, Badge, Field, TextInput,
  TextArea, EmptyState, CoverageBar, IconButton } = window.KeelDesignSystem_7d5998;

function StyleRail({ data, sel, onSelect, q, setQ, facets, setFacets, open, setOpen, collapsed, setCollapsed }) {
  const active = Object.values(facets).reduce((n, a) => n + a.length, 0);
  const items = data.styleFields.filter(f => {
    if (q && !(f.entity + "." + f.field).toLowerCase().includes(q.toLowerCase())) return false;
    if (facets.entity.length && !facets.entity.includes(f.entity)) return false;
    if (facets.orphan.length && !facets.orphan.includes(f.orphan ? "orphan" : "linked")) return false;
    return true;
  });
  const byEntity = {};
  items.forEach(f => { (byEntity[f.entity] = byEntity[f.entity] || []).push(f); });
  return (
    <>
      <RailHeader title="Keel · Style guide" count={items.length + " / " + data.styleFields.length}
        collapsed={collapsed} onCollapse={() => setCollapsed(c => !c)} />
      {collapsed ? null : <>
        <SearchInput placeholder="Filter fields…" value={q} onChange={e => setQ(e.target.value)} />
        <FacetPanel open={open} onOpen={setOpen} activeCount={active} selected={facets}
          onClear={() => setFacets({ entity: [], orphan: [] })}
          onToggle={(k, v) => setFacets(f => ({ ...f, [k]: f[k].includes(v) ? f[k].filter(x => x !== v) : [...f[k], v] }))}
          groups={[
            { key: "entity", label: "Entity", options: ["threat", "mitigation"] },
            { key: "orphan", label: "Model field", options: [["linked","matches the model"],["orphan","orphan"]] },
          ]} />
        <div style={{ overflowY: "auto", flex: 1, minHeight: 0 }}>
          {items.length ? Object.entries(byEntity).map(([ent, fields]) => (
            <div key={ent}>
              <div style={{
                padding: "9px 15px 5px", fontSize: "var(--fs-10)", textTransform: "uppercase",
                letterSpacing: ".07em", color: "var(--text-muted)", fontWeight: "var(--fw-bold)",
                background: "var(--surface-inset)", borderTop: "1px solid var(--line-inner)",
                borderBottom: "1px solid var(--line-inner)",
              }}>{ent}</div>
              {fields.map(f => {
                const on = sel === ent + "." + f.field;
                const tone = f.orphan ? "orphan" : f.pct >= 80 ? "ok" : f.pct >= 40 ? "advice" : "danger";
                return (
                  <div key={f.field} onClick={() => onSelect(ent + "." + f.field)}
                    style={{
                      display: "flex", flexDirection: "row", alignItems: "center", justifyContent: "space-between",
                      gap: "8px", padding: "var(--pad-rail-row)", borderBottom: "1px solid var(--line-inner)",
                      cursor: "pointer", background: on ? "var(--surface-selected)" : "transparent",
                      boxShadow: on ? "var(--selected-rail-accent)" : "none",
                    }}>
                    <span style={{ fontSize: "var(--fs-13)", color: "var(--text-body-read)", fontFamily: "var(--font-mono)" }}>{f.field}</span>
                    <Badge tone={tone} numeric>{f.orphan ? "orphan" : f.pct + "%"}</Badge>
                  </div>
                );
              })}
            </div>
          )) : <EmptyState top="40px">No matches.</EmptyState>}
        </div>
      </>}
    </>
  );
}

const DEFAULT_SLOTS = { purpose: "", include: [], avoid: [], example: "" };

function StyleEditor({ field, onSave }) {
  const [slots, setSlots] = React.useState(field.slots || DEFAULT_SLOTS);
  React.useEffect(() => setSlots(field.slots || DEFAULT_SLOTS), [field.entity, field.field]);
  const list = (key, label, hint) => (
    <SectionBand as="fieldset" label={label} count={(slots[key] || []).length}>
      <Field label="" hint={hint}>
        <ul style={{ listStyle: "none", margin: "6px 0 0", padding: 0 }}>
          {(slots[key] || []).map((v, i) => (
            <li key={i} style={{ display: "flex", gap: "8px", alignItems: "center", marginBottom: "7px" }}>
              <TextInput value={v} onChange={e => setSlots(s => ({ ...s, [key]: s[key].map((x, j) => j === i ? e.target.value : x) }))} />
              <IconButton glyph="×" tone="danger" title="Remove slot"
                onClick={() => setSlots(s => ({ ...s, [key]: s[key].filter((_, j) => j !== i) }))} />
            </li>
          ))}
        </ul>
        <Button size="sm" glyph="＋" onClick={() => setSlots(s => ({ ...s, [key]: [...(s[key] || []), ""] }))}>Add slot</Button>
      </Field>
    </SectionBand>
  );
  return (
    <div>
      <EntityHeader glyph="S" title={field.field} id={field.entity + "." + field.field}
        badges={<>
          {field.orphan ? <Badge tone="orphan">orphan — no matching model field</Badge>
            : <Badge tone={field.pct >= 80 ? "ok" : field.pct >= 40 ? "advice" : "danger"} numeric>{field.pct}% covered</Badge>}
        </>}
        actions={<Button variant="primary" size="sm" onClick={() => onSave(field)}>Save</Button>} />
      <SectionBand as="fieldset" label="Purpose">
        <Field label="" hint="One sentence an author reads before they write the field.">
          <TextArea rows={2} value={slots.purpose} onChange={e => setSlots(s => ({ ...s, purpose: e.target.value }))} />
        </Field>
      </SectionBand>
      {list("include", "What to include", "One line each. These become the bullets in the author's guidance panel.")}
      {list("avoid", "What to avoid", "Name the specific failure, not a generality.")}
      <SectionBand as="fieldset" label="Example">
        <Field label="" hint="A real line from the catalog an author can drop in and adapt.">
          <TextArea rows={2} value={slots.example} onChange={e => setSlots(s => ({ ...s, example: e.target.value }))} />
        </Field>
      </SectionBand>
    </div>
  );
}

/** The right rail earns its column here: exactly what an author sees while you edit. */
function StylePreview({ field }) {
  const s = field.slots;
  if (!s) return <p style={{ color: "var(--text-faint)", fontSize: "var(--fs-13)", fontStyle: "italic" }}>
    No guidance authored for this field yet.</p>;
  return (
    <div style={{ border: "1px solid var(--line-panel)", borderRadius: "var(--r-10)", padding: "14px 15px", background: "var(--surface-inset)" }}>
      <div style={{
        fontSize: "var(--fs-11)", textTransform: "uppercase", letterSpacing: "var(--ls-eyebrow)",
        color: "var(--navy-700)", fontWeight: "var(--fw-bold)", marginBottom: "9px",
      }}>{field.field}</div>
      <p style={{ color: "var(--text-muted)", fontSize: "var(--fs-12)", lineHeight: 1.4, margin: "0 0 6px" }}>{s.purpose}</p>
      <div style={{ background: "#fff", border: "1px solid var(--line-control)", borderRadius: "var(--r-8)", padding: "10px 12px", fontSize: "var(--fs-12)" }}>
        {[["What to include", s.include], ["What to avoid", s.avoid]].map(([k, arr]) => (
          <div key={k} style={{ marginBottom: "8px" }}>
            <span style={{
              display: "block", fontWeight: "var(--fw-bold)", textTransform: "uppercase",
              letterSpacing: var_ls, fontSize: "var(--fs-10)", color: "var(--navy-600)", marginBottom: "3px",
            }}>{k}</span>
            <ul style={{ margin: 0, paddingLeft: "16px", color: "var(--text-body)" }}>
              {arr.map((x, i) => <li key={i} style={{ marginBottom: "2px" }}>{x}</li>)}
            </ul>
          </div>
        ))}
        <div>
          <span style={{
            display: "block", fontWeight: "var(--fw-bold)", textTransform: "uppercase",
            letterSpacing: var_ls, fontSize: "var(--fs-10)", color: "var(--navy-600)", marginBottom: "3px",
          }}>Example</span>
          <p style={{ color: "var(--text-body-read)", fontStyle: "italic", margin: 0 }}>{s.example}</p>
        </div>
      </div>
    </div>
  );
}
const var_ls = ".05em";
Object.assign(window, { StyleRail, StyleEditor, StylePreview });
