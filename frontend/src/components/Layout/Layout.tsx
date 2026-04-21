import type { ReactNode } from "react";
import {
  Header,
  HeaderContainer,
  HeaderName,
  HeaderGlobalBar,
  HeaderGlobalAction,
  SideNav,
  SideNavItems,
  SideNavLink,
  SideNavMenu,
  SideNavMenuItem,
  Theme,
} from "@carbon/react";
import {
  Activity,
  Events,
  Chip,
  ChartLineData,
  GroupResource,
  PolicyIdentity,
  Network_3,
  Notification,
  Search,
  UserAvatar,
} from "@carbon/icons-react";
import { NavLink, useLocation, useNavigate } from "react-router-dom";

export default function Layout({ children }: { children: ReactNode }) {
  const location = useLocation();
  const navigate = useNavigate();

  const is = (p: string) => location.pathname.startsWith(p);

  return (
    <Theme theme="g100">
      <HeaderContainer
        render={() => (
          <div className="optico-layout">
            <Header className="optico-header" aria-label="Optico platform header">
              <HeaderName prefix="Optico" onClick={() => navigate("/")}>
                Agentic ITOps
              </HeaderName>
              <HeaderGlobalBar>
                <HeaderGlobalAction aria-label="Search"><Search /></HeaderGlobalAction>
                <HeaderGlobalAction aria-label="Notifications"><Notification /></HeaderGlobalAction>
                <HeaderGlobalAction aria-label="User"><UserAvatar /></HeaderGlobalAction>
              </HeaderGlobalBar>
            </Header>
            <SideNav
              className="optico-nav"
              isFixedNav
              expanded
              isChildOfHeader={false}
              aria-label="Primary"
            >
              <SideNavItems>
                <SideNavMenu title="Dashboards" renderIcon={ChartLineData} defaultExpanded>
                  <SideNavMenuItem
                    element={NavLink as any}
                    to="/dashboard/roi"
                    isActive={is("/dashboard/roi")}
                  >
                    RoI² Scorecard
                  </SideNavMenuItem>
                  <SideNavMenuItem
                    element={NavLink as any}
                    to="/dashboard/live-ops"
                    isActive={is("/dashboard/live-ops")}
                  >
                    Live Ops
                  </SideNavMenuItem>
                  <SideNavMenuItem
                    element={NavLink as any}
                    to="/dashboard/reliability"
                    isActive={is("/dashboard/reliability")}
                  >
                    Reliability Cockpit
                  </SideNavMenuItem>
                  <SideNavMenuItem
                    element={NavLink as any}
                    to="/dashboard/change-radar"
                    isActive={is("/dashboard/change-radar")}
                  >
                    Change Radar
                  </SideNavMenuItem>
                  <SideNavMenuItem
                    element={NavLink as any}
                    to="/dashboard/infra"
                    isActive={is("/dashboard/infra")}
                  >
                    Infra Health
                  </SideNavMenuItem>
                  <SideNavMenuItem
                    element={NavLink as any}
                    to="/dashboard/cost"
                    isActive={is("/dashboard/cost")}
                  >
                    Cost & Waste
                  </SideNavMenuItem>
                </SideNavMenu>

                <SideNavMenu title="Operations" renderIcon={Events} defaultExpanded>
                  <SideNavMenuItem
                    element={NavLink as any}
                    to="/ops/incidents"
                    isActive={is("/ops/incidents")}
                  >
                    Incident Console
                  </SideNavMenuItem>
                  <SideNavMenuItem
                    element={NavLink as any}
                    to="/ops/hitl"
                    isActive={is("/ops/hitl")}
                  >
                    HITL Queue
                  </SideNavMenuItem>
                  <SideNavMenuItem
                    element={NavLink as any}
                    to="/ops/runbooks"
                    isActive={is("/ops/runbooks")}
                  >
                    Runbooks & KEDB
                  </SideNavMenuItem>
                </SideNavMenu>

                <SideNavMenu title="Platform" renderIcon={GroupResource} defaultExpanded>
                  <SideNavMenuItem
                    element={NavLink as any}
                    to="/platform/agents"
                    isActive={is("/platform/agents")}
                  >
                    Agent Roster
                  </SideNavMenuItem>
                  <SideNavMenuItem
                    element={NavLink as any}
                    to="/platform/tools"
                    isActive={is("/platform/tools")}
                  >
                    MCP Tool Vault
                  </SideNavMenuItem>
                  <SideNavMenuItem
                    element={NavLink as any}
                    to="/platform/kg"
                    isActive={is("/platform/kg")}
                  >
                    Knowledge Graph
                  </SideNavMenuItem>
                  <SideNavMenuItem
                    element={NavLink as any}
                    to="/platform/governance"
                    isActive={is("/platform/governance")}
                  >
                    Governance & Audit
                  </SideNavMenuItem>
                </SideNavMenu>
              </SideNavItems>
            </SideNav>
            <main className="optico-main" role="main">
              {children}
            </main>
          </div>
        )}
      />
    </Theme>
  );
}
