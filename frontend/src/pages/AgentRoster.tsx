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
import { AutonomyTag } from "@/components/Common/AutonomyTag";

export default function AgentRoster() {
  const { data, isLoading } = useQuery({ queryKey: ["agents"], queryFn: api.listAgents });

  if (isLoading || !data) return <SkeletonText paragraph lineCount={5} />;

  const rows = data.map((a) => ({
    id: a.name,
    name: a.display_name,
    workstream: a.workstream,
    autonomy: a.policy?.level ?? a.autonomy_level,
    runs: a.policy?.runs ?? 0,
    accuracy: a.policy ? `${(a.policy.accuracy * 100).toFixed(1)}%` : "—",
    calibration: a.policy ? a.policy.calibration_error.toFixed(2) : "—",
    shadow: a.policy?.shadow_mode ? "shadow" : "",
    kill: a.policy?.kill_switch ? "kill" : "",
  }));

  return (
    <div>
      <Heading>Agent Roster</Heading>
      <p style={{ color: "var(--cds-text-secondary)" }}>
        All registered agents, current autonomy level, performance, and governance flags.
      </p>
      <DataTable
        rows={rows}
        headers={[
          { key: "name", header: "Agent" },
          { key: "workstream", header: "Workstream" },
          { key: "autonomy", header: "Autonomy" },
          { key: "runs", header: "Runs" },
          { key: "accuracy", header: "Accuracy" },
          { key: "calibration", header: "Calib. err" },
          { key: "flags", header: "Flags" },
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
                    if (cell.info.header === "autonomy") {
                      return (
                        <TableCell key={cell.id}>
                          <AutonomyTag level={cell.value as number} />
                        </TableCell>
                      );
                    }
                    if (cell.info.header === "flags") {
                      const src = rows.find((r) => r.id === row.id);
                      return (
                        <TableCell key={cell.id}>
                          {src?.shadow && <Tag type="cyan">shadow</Tag>}
                          {src?.kill && <Tag type="red">kill</Tag>}
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
    </div>
  );
}
