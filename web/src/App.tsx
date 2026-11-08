import { Navigate, Route, Routes, useParams } from "react-router";
import { OverviewPage, ReportsPage, CoveragePage } from "./pages/Overview";
import { LatestReport, ReportPage } from "./pages/Report";
import { FindingPage } from "./pages/Finding";
import { ControlPage, ControlsPage, ThreatPage, ThreatsPage } from "./pages/Library";
import { ComplianceAll, ComplianceSystem } from "./pages/Compliance";
import { ControlEditor, ThreatEditor } from "./pages/Editor";
import { Shell } from "./components/ui";

// Old links keep working: the library editor called controls "mitigations".
const ToControl = () => <Navigate replace to={`/controls/${useParams().id}`} />;

export function App() {
  return (
    <Routes>
      <Route path="/" element={<OverviewPage />} />
      <Route path="/overview" element={<Navigate replace to="/" />} />
      <Route path="/reports" element={<ReportsPage />} />
      <Route path="/reports/:system" element={<LatestReport />} />
      <Route path="/reports/:system/:date" element={<ReportPage />} />
      <Route path="/reports/:system/:date/:finding" element={<FindingPage />} />
      <Route path="/compliance" element={<ComplianceAll />} />
      <Route path="/compliance/:system" element={<ComplianceSystem />} />
      <Route path="/threats" element={<ThreatsPage />} />
      <Route path="/threats/new" element={<ThreatEditor />} />
      <Route path="/threats/:id" element={<ThreatPage />} />
      <Route path="/threats/:id/edit" element={<ThreatEditor />} />
      <Route path="/controls" element={<ControlsPage />} />
      <Route path="/controls/new" element={<ControlEditor />} />
      <Route path="/controls/:id" element={<ControlPage />} />
      <Route path="/controls/:id/edit" element={<ControlEditor />} />
      <Route path="/mitigations" element={<Navigate replace to="/controls" />} />
      <Route path="/mitigations/:id" element={<ToControl />} />
      <Route path="/coverage" element={<CoveragePage />} />
      <Route path="/coverage/:source" element={<CoveragePage />} />
      <Route path="*" element={<Shell title="Not found"><div className="empty"><b>Nothing at this address</b>It may have moved. <a href="/">Back to the overview</a>.</div></Shell>} />
    </Routes>
  );
}
