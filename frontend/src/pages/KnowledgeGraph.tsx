import { useQuery } from "@tanstack/react-query";
import {
  Heading,
  SkeletonText,
  Tile,
  Tag,
} from "@carbon/react";

import { api } from "@/api/client";
import { Section } from "@/components/Common/Section";

export default function KnowledgeGraph() {
  const { data: services, isLoading } = useQuery({
    queryKey: ["kg-services"],
    queryFn: api.listServices,
  });

  if (isLoading || !services) return <SkeletonText paragraph lineCount={4} />;

  return (
    <div>
      <Heading>Knowledge Graph</Heading>
      <p style={{ color: "var(--cds-text-secondary)" }}>
        Services, dependencies, ownership. Every agent grounds its reasoning in this graph.
      </p>
      <Section title="Services">
        <div className="optico-kpi-grid">
          {services.map((s: any) => (
            <ServiceCard key={s.name} name={s.name} tier={s.tier} owner={s.owner} />
          ))}
        </div>
      </Section>
    </div>
  );
}

function ServiceCard({ name, tier, owner }: { name: string; tier?: string; owner?: string }) {
  const { data } = useQuery({
    queryKey: ["kg-ctx", name],
    queryFn: () => api.serviceContext(name),
  });
  return (
    <Tile style={{ padding: "1rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between" }}>
        <strong>{name}</strong>
        <Tag size="sm">tier {tier ?? "?"}</Tag>
      </div>
      <div style={{ fontSize: "0.75rem", color: "var(--cds-text-secondary)" }}>
        owner: {owner ?? "—"}
      </div>
      {data && (
        <div style={{ marginTop: "0.5rem" }}>
          <div style={{ fontSize: "0.75rem", color: "var(--cds-text-secondary)" }}>
            depends on
          </div>
          <div className="optico-badge-row">
            {(data.depends_on as any[])?.map((d: any) => (
              <Tag key={d.name} type="blue" size="sm">
                {d.name}
              </Tag>
            )) || <span>—</span>}
          </div>
        </div>
      )}
    </Tile>
  );
}
