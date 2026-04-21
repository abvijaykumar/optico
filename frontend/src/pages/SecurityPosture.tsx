import { useQuery } from "@tanstack/react-query";
import { Heading, SkeletonText } from "@carbon/react";

import { api } from "@/api/client";
import { KpiCard } from "@/components/Common/Kpi";
import { Section } from "@/components/Common/Section";

export default function SecurityPosture() {
  const { data, isLoading } = useQuery({ queryKey: ["security"], queryFn: api.security });
  if (isLoading || !data) return <SkeletonText paragraph lineCount={4} />;

  return (
    <div>
      <Heading>Risk Posture</Heading>
      <p style={{ color: "var(--cds-text-secondary)" }}>
        Vulnerabilities, policy drift, audit findings.
      </p>
      <Section title="Security">
        <div className="optico-kpi-grid">
          <KpiCard label="Critical CVEs" value={data.vulns_critical as number} />
          <KpiCard label="High CVEs" value={data.vulns_high as number} />
          <KpiCard label="Policy violations" value={data.policy_violations as number} />
          <KpiCard label="MTTR SEV1 (min)" value={data.mttr_minutes_sev1 as number} />
          <KpiCard label="Open audit findings" value={data.audit_findings_open as number} />
        </div>
      </Section>
    </div>
  );
}
