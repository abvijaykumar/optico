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
import { Section } from "@/components/Common/Section";

export default function ReliabilityCockpit() {
  const { data, isLoading } = useQuery({
    queryKey: ["reliability"],
    queryFn: api.reliability,
  });

  if (isLoading || !data) return <SkeletonText paragraph lineCount={5} />;
  const services = data.services as Array<{
    name: string;
    slo: number;
    availability_30d: number;
    error_budget_remaining_pct: number;
    toil_index: number;
  }>;

  return (
    <div>
      <Heading>Reliability Cockpit</Heading>
      <p style={{ color: "var(--cds-text-secondary)" }}>
        SLO burn, error budget, top offenders, toil index.
      </p>

      <Section title="Services">
        <DataTable
          rows={services.map((s) => ({
            id: s.name,
            name: s.name,
            slo: `${(s.slo * 100).toFixed(2)}%`,
            availability: `${(s.availability_30d * 100).toFixed(3)}%`,
            budget: `${(s.error_budget_remaining_pct * 100).toFixed(1)}%`,
            toil: s.toil_index.toFixed(2),
            risk:
              s.error_budget_remaining_pct < 0.25
                ? "At risk"
                : s.error_budget_remaining_pct < 0.5
                ? "Watch"
                : "Healthy",
          }))}
          headers={[
            { key: "name", header: "Service" },
            { key: "slo", header: "SLO" },
            { key: "availability", header: "30d availability" },
            { key: "budget", header: "Error budget" },
            { key: "toil", header: "Toil idx" },
            { key: "risk", header: "Risk" },
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
                        const t =
                          cell.value === "At risk"
                            ? "red"
                            : cell.value === "Watch"
                            ? "warm-gray"
                            : "green";
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
