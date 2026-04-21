import { useQuery } from "@tanstack/react-query";
import { Heading, SkeletonText, Tile, Tag } from "@carbon/react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";

import { api } from "@/api/client";
import { KpiCard } from "@/components/Common/Kpi";
import { Section } from "@/components/Common/Section";

export default function Predictive() {
  const { data, isLoading } = useQuery({ queryKey: ["predictive"], queryFn: api.predictive });
  if (isLoading || !data) return <SkeletonText paragraph lineCount={4} />;

  const drivers = data.top_drivers as Array<Record<string, unknown>>;
  const capacity = data.capacity_projection_7d as Record<string, number>;
  const bars = Object.entries(capacity).map(([name, v]) => ({ name, v: v * 100 }));

  return (
    <div>
      <Heading>Predictive Ops</Heading>
      <p style={{ color: "var(--cds-text-secondary)" }}>
        Forward-looking signals: major-incident probability, capacity breach risk, change-incident correlation.
      </p>

      <Section title="Major Incident — next 4 hours">
        <div className="optico-kpi-grid">
          <KpiCard
            label="Probability"
            value={`${((data.major_incident_prob_next_4h as number) * 100).toFixed(0)}%`}
            hint="platform-wide"
          />
        </div>
        <Tile style={{ padding: "1rem", marginTop: "0.5rem" }}>
          <strong>Top drivers</strong>
          <ul>
            {drivers.map((d, i) => (
              <li key={i}>
                <code>{d.service as string}</code>{" "}
                <Tag size="sm" type="cool-gray">{d.driver as string}</Tag>{" "}
                <Tag size="sm" type="teal">w={((d.weight as number) * 100).toFixed(0)}%</Tag>
              </li>
            ))}
          </ul>
        </Tile>
      </Section>

      <Section title="Capacity — 7-day projection (% utilisation)">
        <Tile style={{ padding: "1rem", height: 260 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={bars}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis unit="%" />
              <Tooltip />
              <Bar dataKey="v" fill="#be95ff" />
            </BarChart>
          </ResponsiveContainer>
        </Tile>
      </Section>
    </div>
  );
}
