import { Route, Routes, Navigate } from "react-router-dom";

import Layout from "./components/Layout/Layout";
import RoIScorecard from "./pages/RoIScorecard";
import LiveOps from "./pages/LiveOps";
import ReliabilityCockpit from "./pages/ReliabilityCockpit";
import ChangeRadar from "./pages/ChangeRadar";
import InfraHealth from "./pages/InfraHealth";
import CostPage from "./pages/CostPage";
import AgentRoster from "./pages/AgentRoster";
import HITLQueue from "./pages/HITLQueue";
import ToolVault from "./pages/ToolVault";
import KnowledgeGraph from "./pages/KnowledgeGraph";
import RunbookLibrary from "./pages/RunbookLibrary";
import Governance from "./pages/Governance";
import IncidentConsole from "./pages/IncidentConsole";

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard/roi" replace />} />
        <Route path="/dashboard/roi" element={<RoIScorecard />} />
        <Route path="/dashboard/live-ops" element={<LiveOps />} />
        <Route path="/dashboard/reliability" element={<ReliabilityCockpit />} />
        <Route path="/dashboard/change-radar" element={<ChangeRadar />} />
        <Route path="/dashboard/infra" element={<InfraHealth />} />
        <Route path="/dashboard/cost" element={<CostPage />} />
        <Route path="/ops/incidents" element={<IncidentConsole />} />
        <Route path="/ops/hitl" element={<HITLQueue />} />
        <Route path="/ops/runbooks" element={<RunbookLibrary />} />
        <Route path="/platform/agents" element={<AgentRoster />} />
        <Route path="/platform/tools" element={<ToolVault />} />
        <Route path="/platform/kg" element={<KnowledgeGraph />} />
        <Route path="/platform/governance" element={<Governance />} />
        <Route path="*" element={<Navigate to="/dashboard/roi" replace />} />
      </Routes>
    </Layout>
  );
}
