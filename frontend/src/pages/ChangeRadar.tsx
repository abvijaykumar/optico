import { useQuery } from "@tanstack/react-query";
import {
  Heading,
  SkeletonText,
  DataTable,
  Table,
  TableHead,
  TableHeader,
  TableRow,
  TableBody,
  TableCell,
  Tag,
} from "@carbon/react";

import { api } from "@/api/client";
import { KpiCard } from "@/components/Common/Kpi";
import { Section } from "@/components/Common/Section";

export default function ChangeRadar() {
  const { data, isLoading } = useQuery({
    queryKey: ["change-radar"],
    queryFn: api.changeRadar,
  });

  if (isLoading || !data) return <SkeletonText paragraph lineCount={5} />;
  const dora = data.dora as Record<string, number>;
  const upcoming = data.upcoming_changes as Array<Record<string, unknown>>;

  return (
    <div>
      <Heading>Change Radar</Heading>
      <p style={{ color: "var(--cds-text-secondary)" }}>
        DORA metrics, change failure rate, upcoming risk heat.
      </p>

      <Section title="DORA">
        <div className="optico-kpi-grid">
          <KpiCard
            label="Change failure rate"
            value={`${(dora.change_failure_rate * 100).toFixed(1)}%`}
          />
          <KpiCard label="Lead time (hr)" value={dora.lead_time_hours} />
          <KpiCard label="Deploys / day" value={dora.deployment_frequency_per_day} />
          <KpiCard label="MTTR (min)" value={dora.mttr_minutes} />
        </div>
      </Section>

      <Section title="Upcoming changes">
        <DataTable
          rows={upcoming.map((c) => ({
            id: c.id as string,
            change: c.id as string,
            service: c.service as string,
            risk: (c.risk as number).toFixed(2),
            scheduled: new Date(c.scheduled as string).toLocaleString(),
            auto: c.auto_approvable ? "Yes" : "No",
          }))}
          headers={[
            { key: "change", header: "Change" },
            { key: "service", header: "Service" },
            { key: "risk", header: "Risk" },
            { key: "scheduled", header: "Scheduled" },
            { key: "auto", header: "Auto-approvable" },
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
                    {row.cells.map((cell) => {
                      if (cell.info.header === "risk") {
                        const n = parseFloat(cell.value as string);
                        const t = n > 0.6 ? "red" : n > 0.3 ? "warm-gray" : "green";
                        return (
                          <TableCell key={cell.id}>
                            <Tag type={t as any}>{cell.value}</Tag>
                          </TableCell>
                        );
                      }
                      return <TableCell key={cell.id}>{cell.value}</TableCell>;
                    })}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </DataTable>
      </Section>
    </div>
  );
}
