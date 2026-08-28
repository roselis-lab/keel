const { RailRow, SearchInput, SectionBand, Card, EntityHeader, Breadcrumb, Button, Badge, RiskBadge,
  EmptyState, WarnBanner } = window.KeelDesignSystem_7d5998;

const RANK = { critical: 0, high: 1, medium: 2, low: 3 };

function ReportsRail({ data, sel, onSelect, q, setQ, collapsed, setCollapsed }) {
  const items = data.reports.filter(r => !q || r.system_name.toLowerCase().includes(q.toLowerCase()));
  return (
    <>
      <RailHeader title="Keel · Reports" count={items.length + " / " + data.reports.length}
        collapsed={collapsed} onCollapse={() => setCollapsed(c => !c)} />
      {collapsed ? null : <>
        <SearchInput placeholder="Filter systems…" value={q} onChange={e => setQ(e.target.value)} />
        <div style={{ overflowY: "auto", flex: 1, minHeight: 0 }}>
          {items.length ? items.map(r => (
            <RailRow key={r.system_id} id={r.system_id} title={r.system_name}
              selected={sel === r.system_id} onClick={() => onSelect(r.system_id)}
              badges={<>
                {r.top_severity ? <RiskBadge level={r.top_severity} /> : null}
                <Badge tone="soft" numeric>{r.latest_date}</Badge>
                <Badge tone="soft" numeric>{r.report_count} runs</Badge>
              </>} />
          )) : <EmptyState top="40px">No matches.</EmptyState>}
        </div>
      </>}
    </>
  );
}

function Finding({ f, rank }) {
  const [open, setOpen] = React.useState(rank === 0);
  return (
    <div style={{
      border: "1px solid var(--line-panel)", borderLeft: "4px solid var(--sev-" + f.severity + "-spine)",
      borderRadius: "var(--r-10)", background: "var(--surface-panel)", marginBottom: "10px", overflow: "hidden",
    }}>
      <div onClick={() => setOpen(o => !o)} style={{ display: "flex", alignItems: "center", gap: "10px", padding: "12px 15px", cursor: "pointer", flexWrap: "wrap" }}>
        <span aria-hidden="true" style={{ color: "var(--text-faint)", fontSize: "var(--fs-10)", width: "10px", flexShrink: 0 }}>{open ? "▾" : "▸"}</span>
        <span style={{
          fontSize: "var(--fs-12)", fontFamily: "var(--font-mono)", color: "var(--text-faint)",
          minWidth: "22px", flexShrink: 0, fontVariantNumeric: "var(--numeric)",
        }}>{rank + 1}.</span>
        <span style={{
          fontFamily: "var(--font-mono)", fontSize: "var(--fs-12)", color: "var(--text-muted)",
          whiteSpace: "nowrap", flexShrink: 0,
        }}>{f.id}</span>
        <RiskBadge level={f.severity} prefix="severity" />
        <RiskBadge level={f.likelihood} prefix="likelihood" />
        <Badge tone="type" mono>{f.harm}</Badge>
        <Badge tone="soft">complexity {f.complexity}</Badge>
      </div>
      {open ? (
        <div style={{ padding: "0 15px 14px" }}>
          <SectionBand label="Scenario" style={{ marginTop: 0 }}><Prose read>{f.scenario}</Prose></SectionBand>
          <SectionBand label="Source">
            <div style={{ display: "grid", gridTemplateColumns: "auto 1fr", gap: "4px 14px", fontSize: "var(--fs-13)" }}>
              {[["who", f.source.who], ["motive", f.source.motive], ["access", f.source.access],
                ["asset", f.asset], ["attack surface", f.attack_surface]].map(([k, v]) => (
                <React.Fragment key={k}>
                  <span style={{ fontSize: "var(--fs-11)", textTransform: "uppercase", letterSpacing: "var(--ls-meta)", color: "var(--text-faint)", paddingTop: "3px" }}>{k}</span>
                  <span style={{ color: "var(--text-body-read)" }}>{v}</span>
                </React.Fragment>
              ))}
            </div>
          </SectionBand>
          <SectionBand label="Vulnerability"><Prose read>{f.vulnerability}</Prose></SectionBand>
          <SectionBand label="Risk" sub={f.severity + " · " + f.likelihood}><Prose read>{f.reasoning}</Prose></SectionBand>
          <SectionBand label="Requirements" count={f.requirements.length}>
            {f.requirements.map((r, i) => (
              <div key={i} style={{ marginTop: i ? "7px" : 0 }}>
                <label style={{ display: "flex", alignItems: "flex-start", gap: "8px", cursor: "pointer", fontSize: "var(--fs-13)", color: "var(--text-body)" }}>
                  <input type="checkbox" defaultChecked={r.status === "already_covered"}
                    style={{ margin: "3px 0 0", flexShrink: 0, accentColor: "var(--accent)" }} />
                  <span>
                    {r.id ? <span style={{ fontFamily: "var(--font-mono)", fontSize: "var(--fs-12)", color: "var(--text-body-read)" }}>{r.id}</span>
                      : <span>{r.description} <Badge tone="advice">ad hoc</Badge></span>}
                    {r.id ? <Badge tone={r.status === "already_covered" ? "ok" : "advice"} style={{ marginLeft: "8px" }}>{r.status}</Badge> : null}
                  </span>
                </label>
                {r.note ? <p style={{ margin: "3px 0 0 24px", color: "var(--text-muted)", fontSize: "var(--fs-12)", fontStyle: "italic", lineHeight: 1.5 }}>{r.note}</p> : null}
              </div>
            ))}
            {f.ignored.length ? f.ignored.map(ig => (
              <p key={ig.id} style={{ marginTop: "9px", color: "var(--text-muted)", fontSize: "var(--fs-12)", fontStyle: "italic", lineHeight: 1.5 }}>
                Ignored — <span style={{ fontFamily: "var(--font-mono)", fontStyle: "normal" }}>{ig.id}</span>: {ig.reason}
              </p>
            )) : null}
          </SectionBand>
          <SectionBand label="Delta" sub="against the previous run"><Prose read>{f.delta}</Prose></SectionBand>
        </div>
      ) : null}
    </div>
  );
}

function ReportScreen({ report, onJump }) {
  const ranked = [...report.findings].sort((a, b) => RANK[a.severity] - RANK[b.severity]);
  return (
    <div>
      <Breadcrumb type="Reports" id={report.system_id + " / " + report.date} />
      <EntityHeader glyph="R" title={report.system_name} id={report.system_id + " · " + report.date}
        badges={<>
          <Badge tone="soft">{report.assessor.split(" <")[0]}</Badge>
          <RiskBadge level={ranked.length ? ranked[0].severity : "info"} prefix={ranked.filter(f => RANK[f.severity] <= 1).length + " at"} />
          <Badge tone="soft" numeric>{report.findings.length} findings</Badge>
          <Badge tone="soft" numeric>{report.discarded.length} discarded</Badge>
        </>}
        actions={<><Button size="sm">Export YAML</Button><Button variant="primary" size="sm">New assessment</Button></>} />

      <SectionBand label="System"><Prose read>{report.system_description}</Prose></SectionBand>
      <SectionBand label="Delta summary" sub="what changed since the last run"><Prose read>{report.delta_summary}</Prose></SectionBand>

      <h3 style={{
        fontSize: "var(--fs-11)", textTransform: "uppercase", letterSpacing: "var(--ls-eyebrow)",
        color: "var(--navy-700)", margin: "24px 0 9px", fontWeight: "var(--fw-bold)",
      }}>Findings <span style={{ fontWeight: "var(--fw-regular)", textTransform: "none", color: "var(--text-faint)" }}>ranked by severity</span></h3>
      {ranked.map((f, i) => <Finding key={f.id} f={f} rank={i} />)}

      <SectionBand label="Discarded" sub="ruled out on reachability, judged un-mitigated" count={report.discarded.length}>
        {report.discarded.map((d, i) => (
          <Card key={d.id} id={d.id} jump onClick={() => onJump(d.id)} desc={d.reason}
            style={i === report.discarded.length - 1 ? { marginBottom: 0 } : null} />
        ))}
      </SectionBand>

      <SectionBand label="Assessor dialogue" sub="the questions that set the grades" count={report.dialogue.length}>
        {report.dialogue.map((d, i) => (
          <Card key={i} style={i === report.dialogue.length - 1 ? { marginBottom: 0 } : null}>
            {[["Q", d.q], ["A", d.a], ["→", d.impact]].map(([k, v]) => (
              <p key={k} style={{ marginTop: k === "Q" ? 0 : "5px", marginBottom: 0, fontSize: "var(--fs-13)", color: k === "→" ? "var(--text-muted)" : "var(--text-body)", lineHeight: 1.55 }}>
                <span style={{ display: "inline-block", minWidth: "18px", fontWeight: "var(--fw-bold)", color: "var(--text-muted)" }}>{k}</span>
                {v}
              </p>
            ))}
          </Card>
        ))}
      </SectionBand>
    </div>
  );
}
Object.assign(window, { ReportsRail, ReportScreen });
