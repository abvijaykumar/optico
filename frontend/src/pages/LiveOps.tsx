import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import {
  Heading,
  Button,
  TextInput,
  Select,
  SelectItem,
  Tile,
  DataTable,
  Table,
  TableHead,
  TableHeader,
  TableRow,
  TableBody,
  TableCell,
  SkeletonText,
} from "@carbon/react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

import { api } from "@/api/client";
import { KpiCard } from "@/components/Common/Kpi";
import { Section } from "@/components/Common/Section";

export default function LiveOps() {
  const live = useQuery({ queryKey: ["live-ops"], queryFn: api.liveOps, refetchInterval: 10_000 });
  const incidents = useQuery({
    queryKey: ["incidents"],
    queryFn: () => api.listIncidents(),
    refetchInterval: 10_000,
  });

  const [service, setService] = useState("checkout");
  const [signal, setSignal] = useState("HighErrorRate");
  const [severity, setSeverity] = useState("SEV2");

  const inject = useMutation({
    mutationFn: () =>
      api.supervisorAlert({
        source: "console",
        service,
        signal,
        severity,
        fingerprint: `manual-${Date.now()}`,
        message: `Manual alert from console`,
      }),
    onSuccess: () => {
      incidents.refetch();
      live.refetch();
    },
  });

  if (live.isLoading || !live.data) return <SkeletonText paragraph lineCount={5} />;
  const mttr = (live.data.mttr_trend_min as number[]).map((v, i) => ({ t: i, v }));

  return (
    <div>
      <Heading>Live Ops</Heading>
      <p style={{ color: "var(--cds-text-secondary)" }}>
        Active incidents, agent actions, HITL queue, timeline.
      </p>

      <Section title="Now">
        <div className="optico-kpi-grid">
          <KpiCard
            label="Active incidents"
            value={(live.data.active_incidents as unknown[]).length}
          />
          <KpiCard label="Agent actions / hr" value={live.data.agent_actions_last_hour as number} />
          <KpiCard label="HITL queue depth" value={live.data.hitl_queue_depth as number} />
        </div>
        <Tile style={{ height: 240, padding: "1rem" }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={mttr}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="t" label={{ value: "days ago", position: "bottom" }} />
              <YAxis label={{ value: "MTTR (min)", angle: -90, position: "insideLeft" }} />
              <Tooltip />
              <Line type="monotone" dataKey="v" stroke="#42be65" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </Tile>
      </Section>

      <Section title="Inject a test alert" action={null}>
        <div style={{ display: "flex", gap: "0.75rem", alignItems: "flex-end", flexWrap: "wrap" }}>
          <TextInput
            id="service"
            labelText="Service"
            value={service}
            onChange={(e) => setService(e.target.value)}
          />
          <TextInput
            id="signal"
            labelText="Signal"
            value={signal}
            onChange={(e) => setSignal(e.target.value)}
          />
          <Select
            id="severity"
            labelText="Severity"
            value={severity}
            onChange={(e) => setSeverity(e.target.value)}
          >
            <SelectItem value="SEV1" text="SEV1" />
            <SelectItem value="SEV2" text="SEV2" />
            <SelectItem value="SEV3" text="SEV3" />
          </Select>
          <Button
            kind="primary"
            onClick={() => inject.mutate()}
            disabled={inject.isPending}
          >
            Fire alert → Supervisor
          </Button>
        </div>
        {inject.isError && (
          <p style={{ color: "var(--cds-support-error)" }}>
            {(inject.error as Error).message}
          </p>
        )}
      </Section>

      <Section title="Recent incidents">
        {incidents.isLoading || !incidents.data ? (
          <SkeletonText paragraph />
        ) : (
          <DataTable
            rows={incidents.data.map((i) => ({
              id: i.id,
              title: i.title,
              severity: i.severity,
              status: i.status,
              services: (i.services || []).join(", "),
              created_at: new Date(i.created_at).toLocaleString(),
            }))}
            headers={[
              { key: "title", header: "Title" },
              { key: "severity", header: "Severity" },
              { key: "status", header: "Status" },
              { key: "services", header: "Services" },
              { key: "created_at", header: "Created" },
            ]}
          >
            {({ rows, headers, getHeaderProps, getTableProps }) => (
              <Table {...getTableProps()}>
                <TableHead>
                  <TableRow>
                    {headers.map((h) => (
                      <TableHeader key={h.key} {...getHeaderProps({ header: h })}>
                        {h.header}
                      </TableHeader>
                    ))}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {rows.map((row) => (
                    <TableRow key={row.id}>
                      {row.cells.map((cell) => (
                        <TableCell key={cell.id}>{cell.value}</TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </DataTable>
        )}
      </Section>
    </div>
  );
}
