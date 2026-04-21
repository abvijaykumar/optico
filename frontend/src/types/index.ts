export type AutonomyLevel = 0 | 1 | 2 | 3 | 4;

export interface AgentDescriptor {
  name: string;
  display_name: string;
  workstream: string;
  description: string;
  autonomy_level: AutonomyLevel;
  tools: string[];
  blast_radius: Record<string, unknown>;
  owner?: string | null;
  policy?: {
    level: AutonomyLevel;
    runs: number;
    accuracy: number;
    calibration_error: number;
    shadow_mode: boolean;
    kill_switch: boolean;
  };
}

export interface ToolCall {
  tool: string;
  args: Record<string, unknown>;
  reason?: string;
}

export interface EvidenceItem {
  source: string;
  kind: string;
  url?: string;
  payload: Record<string, unknown>;
  weight: number;
}

export interface AgentRecommendation {
  id: string;
  agent: string;
  summary: string;
  action?: string;
  tool_calls: ToolCall[];
  confidence: number;
  evidence: EvidenceItem[];
  requires_hitl: boolean;
  autonomy_level: AutonomyLevel;
  created_at: string;
}

export interface AgentRun {
  id: string;
  agent: string;
  input: Record<string, unknown>;
  output?: Record<string, unknown> | null;
  recommendation?: AgentRecommendation | null;
  status: string;
  started_at: string;
  finished_at?: string | null;
  duration_ms?: number | null;
  eval_score?: number | null;
}

export interface HITLItem {
  id: string;
  agent: string;
  recommendation: AgentRecommendation;
  context: Record<string, unknown>;
  urgency: number;
  impact: number;
  created_at: string;
  decided_at?: string | null;
  decision?: "approve" | "reject" | "edit" | "escalate" | null;
  decided_by?: string | null;
  decision_notes?: string | null;
}

export interface Incident {
  id: string;
  title: string;
  summary: string;
  severity: "SEV1" | "SEV2" | "SEV3" | "SEV4";
  status: string;
  services: string[];
  alerts: string[];
  linked_changes: string[];
  timeline: Array<Record<string, unknown>>;
  commander?: string | null;
  created_at: string;
  updated_at: string;
  mttr_seconds?: number | null;
}

export interface RoIMetrics {
  decision_yield: Record<string, number>;
  learning_velocity: Record<string, number>;
  cognitive_leverage: Record<string, number>;
  financial: Record<string, number>;
  generated_at: string;
}
