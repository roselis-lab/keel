const { StatTile, CoverageBar, SplitBar, GapChips, WarnBanner, Badge } = window.KeelDesignSystem_7d5998;

function OverviewScreen({ data, onJump }) {
  const s = data.stats, cov = data.coverage;
  // Both halves come from stats, not from the 6-row sample in data.mitigations.
  const verified = s.verified;
  return (
    <div>
      <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
        <StatTile value={s.threats} label="threats" />
        <StatTile value={s.mitigations} label="mitigations" />
        <StatTile value={s.links} label="mitigation links" />
        <StatTile value={s.systems} label="systems assessed" />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", alignItems: "start", marginTop: "16px" }}>
        <PanelCard label="Style-guide coverage">
          <div style={{ display: "flex", alignItems: "baseline", gap: "10px", marginBottom: "10px" }}>
            <span style={{ fontSize: "var(--fs-24)", fontWeight: "var(--fw-bold)", letterSpacing: "var(--ls-number)", fontVariantNumeric: "var(--numeric)" }}>{cov.overall}%</span>
            <span style={{ fontSize: "var(--fs-12)", color: "var(--text-muted)" }}>of model fields carry authoring guidance</span>
          </div>
          {cov.entities.map(e => <CoverageBar key={e.entity} label={e.entity} percent={e.overall} />)}
          {cov.entities[0].fields.map(f => <CoverageBar key={f.name} label={f.name} percent={f.pct} orphan={f.orphan} />)}
        </PanelCard>

        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <PanelCard label="Mitigation status">
            <SplitBar segments={[
              { tone: "verified", label: "verified", value: verified },
              { tone: "draft", label: "draft", value: s.mitigations - verified },
            ]} />
            <h3 style={{ fontSize: "var(--fs-11)", textTransform: "uppercase", letterSpacing: "var(--ls-eyebrow)", color: "var(--navy-700)", margin: "16px 0 0", fontWeight: "var(--fw-bold)" }}>Implementations recorded</h3>
            <SplitBar segments={[
              { tone: "ok", label: "recorded", value: s.implementations_recorded },
              { tone: "unset", label: "empty", value: s.mitigations - s.implementations_recorded },
            ]} />
          </PanelCard>
          <PanelCard label="Recent activity">
            {data.activity.map((a, i) => (
              <div key={i} style={{
                display: "flex", alignItems: "baseline", gap: "8px", padding: "7px 0",
                borderBottom: i === data.activity.length - 1 ? "none" : "1px solid var(--line-inner)",
                fontSize: "var(--fs-13)", flexWrap: "wrap",
              }}>
                <span style={{ color: "var(--text-body-read)" }}>{a.msg}</span>
                <span style={{ color: "var(--text-muted)", fontSize: "var(--fs-12)", fontFamily: "var(--font-mono)" }}>{a.meta}</span>
              </div>
            ))}
          </PanelCard>
        </div>
      </div>

      <div style={{ marginTop: "16px" }}>
        <PanelCard label="Gaps to review">
          <p style={{ color: "var(--text-muted)", fontSize: "var(--fs-12)", margin: "0 0 12px" }}>
            Nothing here blocks anything. It is a place to see where the model is thin.
          </p>
          {data.gaps.map(g => (
            <div key={g.name} style={{ marginBottom: "10px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <span style={{ fontWeight: "var(--fw-semibold)", color: "var(--text-body-read)", fontSize: "var(--fs-14)" }}>{g.name}</span>
                <Badge tone="danger" numeric>{g.ids.length}</Badge>
              </div>
              <p style={{ color: "var(--text-muted)", fontSize: "var(--fs-12)", margin: "4px 0 0" }}>{g.desc}</p>
              <GapChips label="" items={g.ids.map(i => [i.split(" ::")[0], i])} onPick={onJump} dashed={false} style={{ marginTop: "4px" }} />
            </div>
          ))}
        </PanelCard>
      </div>
    </div>
  );
}
Object.assign(window, { OverviewScreen });
