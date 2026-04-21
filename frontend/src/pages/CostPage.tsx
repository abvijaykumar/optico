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
} from "@carbon/react";

import { api } from "@/api/client";
import { KpiCard } from "@/components/Common/Kpi";
import { Section } from "@/components/Common/Section";

export default function CostPage() {
  const { data, isLoading } = useQuery({ queryKey: ["cost"], queryFn: api.cost });
  if (isLoading || !data) return <SkeletonText paragraph lineCount={3} />;

  const anomalies = data.anomalies as Array<Record<string, unknown>>;

  return (
    <div>
      <Heading>Cost & Waste</Heading>
      <Section title="Spend">
        <div className="optico-kpi-grid">
          <KpiCard
            label="Monthly spend"
            value={`$${(data.monthly_spend_usd as number).toLocaleString()}`}
          />
          <KpiCard
            label="Idle resources"
            value={`$${(data.idle_resources_usd as number).toLocaleString()}`}
            hint="rightsizing candidates"
          />
        </div>
      </Section>

      <Section title="Cost anomalies">
        <DataTable
          rows={anomalies.map((a) => ({
            id: a.service as string,
            service: a.service as string,
            delta: `${(((a.delta_pct as number) || 0) * 100).toFixed(1)}%`,
            cause: a.likely_cause as string,
          }))}
          headers={[
            { key: "service", header: "Service" },
            { key: "delta", header: "Δ" },
            { key: "cause", header: "Likely cause" },
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
      </Section>
    </div>
  );
}
