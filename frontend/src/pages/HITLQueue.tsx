import { useEffect, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Heading,
  Tile,
  SkeletonText,
  Tag,
  Button,
  TextArea,
  Accordion,
  AccordionItem,
} from "@carbon/react";

import { api, hitlSocket } from "@/api/client";
import { Section } from "@/components/Common/Section";
import { AutonomyTag } from "@/components/Common/AutonomyTag";
import type { HITLItem } from "@/types";

export default function HITLQueue() {
  const qc = useQueryClient();
  const queue = useQuery({
    queryKey: ["hitl"],
    queryFn: () => api.listHITL(false),
    refetchInterval: 15_000,
  });

  // Live stream from WebSocket.
  useEffect(() => {
    const ws = hitlSocket(() => qc.invalidateQueries({ queryKey: ["hitl"] }));
    return () => ws.close();
  }, [qc]);

  const decide = useMutation({
    mutationFn: ({
      id,
      decision,
      notes,
    }: {
      id: string;
      decision: "approve" | "reject" | "escalate";
      notes?: string;
    }) =>
      api.decideHITL(id, { decision, decided_by: "operator@optico", notes }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["hitl"] }),
  });

  if (queue.isLoading || !queue.data) return <SkeletonText paragraph lineCount={5} />;
  const items = queue.data;

  return (
    <div>
      <Heading>HITL Queue</Heading>
      <p style={{ color: "var(--cds-text-secondary)" }}>
        Ranked by urgency × impact. Every item shows the agent's evidence chain.
      </p>
      {items.length === 0 && (
        <Tile style={{ padding: "1rem" }}>Queue is empty — no pending decisions.</Tile>
      )}
      {items.map((item) => (
        <QueueCard
          key={item.id}
          item={item}
          onDecide={(decision, notes) =>
            decide.mutate({ id: item.id, decision, notes })
          }
        />
      ))}
    </div>
  );
}

function QueueCard({
  item,
  onDecide,
}: {
  item: HITLItem;
  onDecide: (d: "approve" | "reject" | "escalate", notes?: string) => void;
}) {
  const [notes, setNotes] = useState("");
  const rec = item.recommendation;

  return (
    <Section
      title={rec.summary}
      action={
        <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
          <Tag type="purple">{item.agent}</Tag>
          <AutonomyTag level={rec.autonomy_level} />
          <Tag type={item.urgency <= 1 ? "red" : item.urgency <= 2 ? "warm-gray" : "cool-gray"}>
            U{item.urgency}·I{item.impact}
          </Tag>
          <Tag type="green">{Math.round(rec.confidence * 100)}%</Tag>
        </div>
      }
    >
      <Tile style={{ padding: "1rem" }}>
        <div style={{ fontSize: "0.875rem", color: "var(--cds-text-secondary)", marginBottom: "0.5rem" }}>
          Action: <code>{rec.action || "—"}</code>
        </div>
        {rec.tool_calls.length > 0 && (
          <div style={{ marginBottom: "0.5rem" }}>
            <strong>Proposed tool calls</strong>
            <ul>
              {rec.tool_calls.map((tc, i) => (
                <li key={i}>
                  <code>{tc.tool}</code>
                  {tc.reason && <span style={{ color: "var(--cds-text-secondary)" }}> — {tc.reason}</span>}
                </li>
              ))}
            </ul>
          </div>
        )}
        <Accordion>
          <AccordionItem title={`Evidence (${rec.evidence.length})`}>
            <pre className="optico-evidence">{JSON.stringify(rec.evidence, null, 2)}</pre>
          </AccordionItem>
        </Accordion>
        <TextArea
          id={`notes-${item.id}`}
          labelText="Decision notes"
          placeholder="Optional context for the audit trail"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          rows={2}
          style={{ marginTop: "0.75rem" }}
        />
        <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.75rem" }}>
          <Button kind="primary" onClick={() => onDecide("approve", notes)}>
            Approve
          </Button>
          <Button kind="danger--tertiary" onClick={() => onDecide("reject", notes)}>
            Reject
          </Button>
          <Button kind="tertiary" onClick={() => onDecide("escalate", notes)}>
            Escalate
          </Button>
        </div>
      </Tile>
    </Section>
  );
}
