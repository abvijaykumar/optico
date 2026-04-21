import { useQuery } from "@tanstack/react-query";
import { Heading, Tile, SkeletonText } from "@carbon/react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

import { api } from "@/api/client";
import { KpiCard } from "@/components/Common/Kpi";
import { Section } from "@/components/Common/Section";

export default function RoIScorecard() {
  const { data, isLoading } = useQuery({
    queryKey: ["roi"],
    queryFn: api.roi,
  });

  if (isLoading || !data) {
    return <SkeletonText paragraph lineCount={5} />;
  }

  const pct = (v: number) => `${(v * 100).toFixed(1)}%`;

  const decisionChart = [
    { name: "Auto-triaged", value: data.decision_yield.alerts_auto_triaged_pct * 100 },
    { name: "MTTR Δ", value: data.decision_yield.mttr_reduction_pct * 100 },
    {
      name: "Change Fail Δ",
      value: data.decision_yield.change_failure_rate_reduction_pct * 100,
    },
  ];

  return (
    <div>
      <Heading>RoI² Scorecard</Heading>
      <p style={{ color: "var(--cds-text-secondary)" }}>
        Decision Yield · Learning Velocity · Cognitive Leverage · Financial
      </p>

      <Section title="Decision Yield">
        <div className="optico-kpi-grid">
          <KpiCard
            label="Alerts auto-triaged"
            value={pct(data.decision_yield.alerts_auto_triaged_pct)}
            hint="Target 85%"
          />
          <KpiCard
            label="MTTR reduction"
            value={pct(data.decision_yield.mttr_reduction_pct)}
            hint="vs. baseline"
          />
          <KpiCard
            label="Change failure rate Δ"
            value={pct(data.decision_yield.change_failure_rate_reduction_pct)}
          />
        </div>
        <Tile style={{ padding: "1rem", height: 240 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={decisionChart}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis unit="%" />
              <Tooltip />
              <Bar dataKey="value" fill="#4589ff" />
            </BarChart>
          </ResponsiveContainer>
        </Tile>
      </Section>

      <Section title="Learning Velocity">
        <div className="optico-kpi-grid">
          <KpiCard
            label="Runbooks generated / 30d"
            value={data.learning_velocity.runbooks_generated_last_30d}
          />
          <KpiCard
            label="KEDB entries / 30d"
            value={data.learning_velocity.kedb_entries_last_30d}
          />
          <KpiCard
            label="Days → automation"
            value={data.learning_velocity.days_to_automation}
            hint="Target < 14"
          />
        </div>
      </Section>

      <Section title="Cognitive Leverage">
        <div className="optico-kpi-grid">
          <KpiCard
            label="Toil hrs reclaimed / wk"
            value={data.cognitive_leverage.toil_hours_reclaimed_per_week}
          />
          <KpiCard
            label="Agents at L2+"
            value={data.cognitive_leverage.agents_at_l2_plus}
            hint="Target 15+"
          />
          <KpiCard
            label="Incidents w/ drafted PIR"
            value={pct(data.cognitive_leverage.pct_incidents_with_drafted_pir)}
          />
        </div>
      </Section>

      <Section title="Financial">
        <div className="optico-kpi-grid">
          <KpiCard
            label="Ops cost Δ"
            value={pct(data.financial.ops_cost_delta_pct)}
            hint="vs. baseline"
          />
          <KpiCard
            label="Avoided downtime (30d)"
            value={`$${data.financial.avoided_downtime_usd_30d.toLocaleString()}`}
          />
        </div>
      </Section>
    </div>
  );
}
