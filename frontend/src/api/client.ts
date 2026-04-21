import type {
  AgentDescriptor,
  AgentRun,
  HITLItem,
  Incident,
  RoIMetrics,
} from "@/types";

const base = "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${base}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    throw new Error(`${res.status} ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () => request<{ status: string }>("/../health"),

  // agents
  listAgents: () => request<AgentDescriptor[]>("/agents"),
  runAgent: (name: string, payload: unknown) =>
    request<AgentRun>(`/agents/${name}/run`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  supervisorAlert: (alert: unknown) =>
    request<Record<string, unknown>>(`/agents/supervisor/alert`, {
      method: "POST",
      body: JSON.stringify(alert),
    }),

  // incidents
  listIncidents: (status?: string) =>
    request<Incident[]>(`/incidents${status ? `?status=${status}` : ""}`),
  getIncident: (id: string) => request<Incident>(`/incidents/${id}`),

  // changes
  listChanges: () => request<unknown[]>("/changes"),
  scoreChange: (id: string) =>
    request<AgentRun>(`/changes/${id}/score`, { method: "POST" }),

  // HITL
  listHITL: (includeDecided = false) =>
    request<HITLItem[]>(`/hitl/queue?include_decided=${includeDecided}`),
  decideHITL: (id: string, body: {
    decision: "approve" | "reject" | "edit" | "escalate";
    decided_by: string;
    notes?: string;
  }) =>
    request<HITLItem>(`/hitl/${id}/decide`, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  // MCP
  listServers: () => request<Array<Record<string, unknown>>>("/mcp/servers"),
  callTool: (tool: string, args: Record<string, unknown>) =>
    request<Record<string, unknown>>(`/mcp/call`, {
      method: "POST",
      body: JSON.stringify({ tool, args }),
    }),

  // KG
  listServices: () => request<Array<Record<string, unknown>>>("/kg/services"),
  serviceContext: (name: string) =>
    request<Record<string, unknown>>(`/kg/services/${encodeURIComponent(name)}/context`),

  // runbooks / KEDB
  listRunbooks: () => request<Array<Record<string, unknown>>>("/runbooks"),
  listKEDB: (q = "") =>
    request<Array<Record<string, unknown>>>(`/runbooks/kedb?query=${encodeURIComponent(q)}`),

  // dashboards
  roi: () => request<RoIMetrics>("/dashboards/roi"),
  liveOps: () => request<Record<string, unknown>>("/dashboards/live-ops"),
  reliability: () => request<Record<string, unknown>>("/dashboards/reliability"),
  changeRadar: () => request<Record<string, unknown>>("/dashboards/change-radar"),
  infraHealth: () => request<Record<string, unknown>>("/dashboards/infra-health"),
  cost: () => request<Record<string, unknown>>("/dashboards/cost"),

  // governance
  listPolicies: () => request<Array<Record<string, unknown>>>("/governance/policies"),
  promote: (agent: string) =>
    request<{ ok: boolean; reason: string; level: number }>(
      `/governance/policies/${agent}/promote`,
      { method: "POST" },
    ),
  setKillSwitch: (agent: string, engaged: boolean) =>
    request<Record<string, unknown>>(
      `/governance/policies/${agent}/kill-switch`,
      { method: "POST", body: JSON.stringify({ engaged }) },
    ),
  setShadowMode: (agent: string, engaged: boolean) =>
    request<Record<string, unknown>>(
      `/governance/policies/${agent}/shadow-mode`,
      { method: "POST", body: JSON.stringify({ engaged }) },
    ),
  audit: () => request<Array<Record<string, unknown>>>("/governance/audit"),
};

export function hitlSocket(onMessage: (event: unknown) => void): WebSocket {
  const proto = window.location.protocol === "https:" ? "wss" : "ws";
  const host = window.location.host;
  const ws = new WebSocket(`${proto}://${host}/api/hitl/stream`);
  ws.onmessage = (evt) => {
    try {
      onMessage(JSON.parse(evt.data));
    } catch {
      /* ignore */
    }
  };
  return ws;
}
