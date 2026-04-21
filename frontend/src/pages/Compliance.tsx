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

const STATUS_COLOUR: Record<string, string> = {
  implemented: "green",
  inherited: "teal",
  planned: "warm-gray",
  gap: "red",
};

export default function Compliance() {
  const { data, isLoading } = useQuery({ queryKey: ["fedramp"], queryFn: api.fedramp });
  if (isLoading || !data) return <SkeletonText paragraph lineCount={5} />;

  const summary = data.summary as Record<string, number>;
  const controls = data.controls as Array<Record<string, unknown>>;

  return (
    <div>
      <Heading>Compliance — FedRAMP</Heading>
      <p style={{ color: "var(--cds-text-secondary)" }}>
        NIST 800-53 Rev.5 control posture, continuously verified by the Compliance Agent.
      </p>

      <Section title="Summary">
        <div className="optico-kpi-grid">
          <KpiCard label="Implemented" value={summary.implemented} />
          <KpiCard label="Inherited" value={summary.inherited} />
          <KpiCard label="Planned" value={summary.planned} />
          <KpiCard label="Gap" value={summary.gap} />
        </div>
      </Section>

      <Section title="Controls">
        <DataTable
          rows={controls.map((c) => ({
            id: c.id as string,
            control: c.id as string,
            name: c.name as string,
            family: c.family as string,
            status: c.status as string,
            evidence: (c.evidence as string) ?? "—",
          }))}
          headers={[
            { key: "control", header: "ID" },
            { key: "name", header: "Name" },
            { key: "family", header: "Family" },
            { key: "status", header: "Status" },
            { key: "evidence", header: "Evidence" },
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
                      if (cell.info.header === "status") {
                        return (
                          <TableCell key={cell.id}>
                            <Tag type={(STATUS_COLOUR[cell.value as string] ?? "cool-gray") as any}>
                              {cell.value}
                            </Tag>
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
