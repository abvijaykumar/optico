import { useQuery } from "@tanstack/react-query";
import { Heading, SkeletonText, Tile, Tag, Accordion, AccordionItem } from "@carbon/react";

import { api } from "@/api/client";
import { AutonomyTag } from "@/components/Common/AutonomyTag";
import { Section } from "@/components/Common/Section";

const WORKSTREAM_LABEL: Record<string, string> = {
  incident: "Incident",
  release: "Release",
  sre: "SRE",
  stack: "Full-stack",
  analytics: "Analytics",
  platform: "Platform",
};

/**
 * StackHealth is a grouped view of all "stack" workstream agents —
 * hardware, platform, middleware, application — organised by layer.
 */
export default function StackHealth() {
  const { data, isLoading } = useQuery({ queryKey: ["agents"], queryFn: api.listAgents });
  if (isLoading || !data) return <SkeletonText paragraph lineCount={6} />;

  const groups = {
    Hardware: ["hw-health-agent", "disk-failure-agent", "firmware-agent", "net-fabric-agent", "power-thermal-agent"],
    Platform: ["cloud-optimizer-agent", "iac-drift-agent", "os-patching-agent", "storage-agent",
               "net-policy-agent", "cert-agent", "backup-dr-agent"],
    Middleware: ["dba-agent", "broker-agent", "api-gw-agent", "mesh-agent", "cache-agent",
                 "runtime-agent", "lb-agent"],
    Application: ["apm-agent", "log-analysis-agent", "trace-agent", "rum-agent", "synthetic-agent",
                  "feature-perf-agent", "session-replay-agent"],
  } as const;

  return (
    <div>
      <Heading>Full-Stack Health</Heading>
      <p style={{ color: "var(--cds-text-secondary)" }}>
        Agents across Hardware → Platform → Middleware → Application layers.
      </p>
      {Object.entries(groups).map(([layer, names]) => {
        const rows = data.filter((a) => names.includes(a.name));
        return (
          <Section key={layer} title={layer}>
            <div className="optico-kpi-grid">
              {rows.map((a) => (
                <Tile key={a.name} style={{ padding: "1rem" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <strong>{a.display_name}</strong>
                    <AutonomyTag level={a.policy?.level ?? a.autonomy_level} />
                  </div>
                  <div style={{ fontSize: "0.75rem", color: "var(--cds-text-secondary)", marginTop: "0.25rem" }}>
                    {WORKSTREAM_LABEL[a.workstream] ?? a.workstream} · {a.tools.length} tools
                  </div>
                  <Accordion style={{ marginTop: "0.5rem" }}>
                    <AccordionItem title="Tools">
                      <div className="optico-badge-row">
                        {a.tools.map((t) => (
                          <Tag key={t} type="cool-gray" size="sm">{t}</Tag>
                        ))}
                      </div>
                    </AccordionItem>
                  </Accordion>
                </Tile>
              ))}
            </div>
          </Section>
        );
      })}
    </div>
  );
}
