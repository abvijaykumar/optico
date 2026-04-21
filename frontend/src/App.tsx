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
import StackHealth from "./pages/StackHealth";
import SecurityPosture from "./pages/SecurityPosture";
import Predictive from "./pages/Predictive";
import Federation from "./pages/Federation";
import Compliance from "./pages/Compliance";

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard/roi" replace />} />

        {/* Dashboards */}
        <Route path="/dashboard/roi" element={<RoIScorecard />} />
        <Route path="/dashboard/live-ops" element={<LiveOps />} />
        <Route path="/dashboard/reliability" element={<ReliabilityCockpit />} />
        <Route path="/dashboard/change-radar" element={<ChangeRadar />} />
        <Route path="/dashboard/infra" element={<InfraHealth />} />
        <Route path="/dashboard/cost" element={<CostPage />} />
        <Route path="/dashboard/security" element={<SecurityPosture />} />
        <Route path="/dashboard/predictive" element={<Predictive />} />

        {/* Operations */}
        <Route path="/ops/incidents" element={<IncidentConsole />} />
        <Route path="/ops/hitl" element={<HITLQueue />} />
        <Route path="/ops/runbooks" element={<RunbookLibrary />} />
        <Route path="/ops/stack" element={<StackHealth />} />

        {/* Platform */}
        <Route path="/platform/agents" element={<AgentRoster />} />
        <Route path="/platform/tools" element={<ToolVault />} />
        <Route path="/platform/kg" element={<KnowledgeGraph />} />
        <Route path="/platform/governance" element={<Governance />} />
        <Route path="/platform/federation" element={<Federation />} />
        <Route path="/platform/compliance" element={<Compliance />} />

        <Route path="*" element={<Navigate to="/dashboard/roi" replace />} />
      </Routes>
    </Layout>
  );
}
