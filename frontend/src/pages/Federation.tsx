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

export default function Federation() {
  const clusters = useQuery({ queryKey: ["clusters"], queryFn: api.listClusters });
  const tenants = useQuery({ queryKey: ["tenants"], queryFn: api.listTenants });

  if (clusters.isLoading || !clusters.data || tenants.isLoading || !tenants.data) {
    return <SkeletonText paragraph lineCount={5} />;
  }

  return (
    <div>
      <Heading>Federation & Tenancy</Heading>
      <p style={{ color: "var(--cds-text-secondary)" }}>
        Multi-cluster control-plane topology, tenant isolation, and data-residency profile per cluster.
      </p>

      <Section title="Clusters">
        <DataTable
          rows={(clusters.data as any[]).map((c) => ({
            id: c.id,
            name: c.name,
            region: c.region,
            profile: c.profile,
            tenants: (c.tenant_ids as string[]).join(", "),
            enclave: c.enclave ? "yes" : "no",
          }))}
          headers={[
            { key: "name", header: "Cluster" },
            { key: "region", header: "Region" },
            { key: "profile", header: "Profile" },
            { key: "tenants", header: "Tenants" },
            { key: "enclave", header: "FedRAMP enclave" },
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
                      if (cell.info.header === "profile") {
                        const type = cell.value === "fedramp" ? "magenta"
                                    : cell.value === "eu-data-residency" ? "teal" : "cool-gray";
                        return (
                          <TableCell key={cell.id}>
                            <Tag type={type as any}>{cell.value}</Tag>
                          </TableCell>
                        );
                      }
                      if (cell.info.header === "enclave") {
                        return (
                          <TableCell key={cell.id}>
                            {cell.value === "yes" ? <Tag type="red">enclave</Tag> : "—"}
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

      <Section title="Tenants">
        <DataTable
          rows={(tenants.data as any[]).map((t) => ({
            id: t.id,
            name: t.name,
            cluster: t.cluster_id,
            owner: t.owner ?? "—",
            data_class: t.data_class,
            retention: `${t.retention_days}d`,
          }))}
          headers={[
            { key: "name", header: "Tenant" },
            { key: "cluster", header: "Cluster-of-record" },
            { key: "owner", header: "Owner" },
            { key: "data_class", header: "Data class" },
            { key: "retention", header: "Retention" },
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
                      if (cell.info.header === "data_class") {
                        const type = cell.value === "regulated" ? "red"
                                   : cell.value === "restricted" ? "warm-gray" : "green";
                        return (
                          <TableCell key={cell.id}>
                            <Tag type={type as any}>{cell.value}</Tag>
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
