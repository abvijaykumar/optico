import { useQuery } from "@tanstack/react-query";
import { Heading, SkeletonText } from "@carbon/react";

import { api } from "@/api/client";
import { KpiCard } from "@/components/Common/Kpi";
import { Section } from "@/components/Common/Section";

export default function InfraHealth() {
  const { data, isLoading } = useQuery({ queryKey: ["infra"], queryFn: api.infraHealth });

  if (isLoading || !data) return <SkeletonText paragraph lineCount={4} />;
  const hosts = data.hosts as Record<string, number>;
  const k8s = data.k8s as Record<string, number>;

  return (
    <div>
      <Heading>Infra Health</Heading>
      <Section title="Hardware">
        <div className="optico-kpi-grid">
          <KpiCard label="Hosts total" value={hosts.total} />
          <KpiCard label="Healthy" value={hosts.healthy} />
          <KpiCard label="Degraded" value={hosts.degraded} />
          <KpiCard label="Failed" value={hosts.failed} />
        </div>
      </Section>

      <Section title="Kubernetes">
        <div className="optico-kpi-grid">
          <KpiCard label="Clusters" value={k8s.clusters} />
          <KpiCard label="Nodes" value={k8s.nodes} />
          <KpiCard label="Pending pods" value={k8s.pods_pending} />
        </div>
      </Section>

      <Section title="Compliance">
        <KpiCard
          label="Patch compliance"
          value={`${((data.patch_compliance_pct as number) * 100).toFixed(1)}%`}
        />
      </Section>
    </div>
  );
}
