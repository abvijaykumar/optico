import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Heading,
  SkeletonText,
  Tile,
  Tag,
  Accordion,
  AccordionItem,
} from "@carbon/react";

import { api } from "@/api/client";
import { Section } from "@/components/Common/Section";

export default function IncidentConsole() {
  const { data, isLoading } = useQuery({
    queryKey: ["incidents-console"],
    queryFn: () => api.listIncidents(),
    refetchInterval: 10_000,
  });

  if (isLoading || !data) return <SkeletonText paragraph lineCount={6} />;

  return (
    <div>
      <Heading>Incident Console</Heading>
      <p style={{ color: "var(--cds-text-secondary)" }}>
        Every active incident, its agent trail, and evidence chain.
      </p>
      {data.length === 0 && (
        <Tile style={{ padding: "1rem" }}>
          No active incidents. Use <code>Live Ops → Inject a test alert</code> to trigger the pipeline.
        </Tile>
      )}
      {data.map((inc) => (
        <Section
          key={inc.id}
          title={inc.title}
          action={
            <div style={{ display: "flex", gap: "0.5rem" }}>
              <Tag type="red">{inc.severity}</Tag>
              <Tag>{inc.status}</Tag>
            </div>
          }
        >
          <Tile style={{ padding: "1rem" }}>
            <p>{inc.summary}</p>
            <div style={{ marginTop: "0.5rem", fontSize: "0.75rem", color: "var(--cds-text-secondary)" }}>
              Services: {(inc.services || []).join(", ") || "—"} · Opened: {new Date(inc.created_at).toLocaleString()}
            </div>
            <Accordion style={{ marginTop: "0.75rem" }}>
              <AccordionItem title="Timeline">
                <ol>
                  {(inc.timeline || []).map((t: any, i: number) => (
                    <li key={i}>
                      <code>{t.ts}</code> — {t.event}
                    </li>
                  ))}
                </ol>
              </AccordionItem>
              <AccordionItem title="Raw">
                <pre className="optico-evidence">{JSON.stringify(inc, null, 2)}</pre>
              </AccordionItem>
            </Accordion>
          </Tile>
        </Section>
      ))}
    </div>
  );
}
