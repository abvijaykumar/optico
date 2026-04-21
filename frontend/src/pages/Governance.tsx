import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
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
  Button,
  Tag,
  Tile,
} from "@carbon/react";

import { api } from "@/api/client";
import { AutonomyTag } from "@/components/Common/AutonomyTag";
import { Section } from "@/components/Common/Section";

export default function Governance() {
  const qc = useQueryClient();
  const policies = useQuery({ queryKey: ["policies"], queryFn: api.listPolicies });
  const audit = useQuery({ queryKey: ["audit"], queryFn: api.audit, refetchInterval: 10_000 });

  const promote = useMutation({
    mutationFn: (agent: string) => api.promote(agent),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["policies"] }),
  });
  const kill = useMutation({
    mutationFn: (p: { agent: string; engaged: boolean }) =>
      api.setKillSwitch(p.agent, p.engaged),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["policies"] }),
  });
  const shadow = useMutation({
    mutationFn: (p: { agent: string; engaged: boolean }) =>
      api.setShadowMode(p.agent, p.engaged),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["policies"] }),
  });

  if (policies.isLoading || !policies.data) return <SkeletonText paragraph lineCount={5} />;

  const rows = (policies.data as any[]).map((p) => ({
    id: p.agent,
    agent: p.agent,
    level: p.level,
    runs: p.runs,
    accuracy: `${(p.accuracy * 100).toFixed(1)}%`,
    calibration: p.calibration_error.toFixed(2),
    shadow: p.shadow_mode,
    kill: p.kill_switch,
  }));

  return (
    <div>
      <Heading>Governance & Audit</Heading>
      <p style={{ color: "var(--cds-text-secondary)" }}>
        Autonomy policies per agent, kill-switches, shadow mode, immutable audit log.
      </p>

      <Section title="Autonomy policies">
        <DataTable
          rows={rows}
          headers={[
            { key: "agent", header: "Agent" },
            { key: "level", header: "Level" },
            { key: "runs", header: "Runs" },
            { key: "accuracy", header: "Accuracy" },
            { key: "calibration", header: "Calib" },
            { key: "flags", header: "Flags" },
            { key: "actions", header: "Actions" },
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
                {rows.map((row) => {
                  const src = (policies.data as any[]).find((p) => p.agent === row.id)!;
                  return (
                    <TableRow key={row.id}>
                      {row.cells.map((cell) => {
                        if (cell.info.header === "level") {
                          return (
                            <TableCell key={cell.id}>
                              <AutonomyTag level={cell.value as number} />
                            </TableCell>
                          );
                        }
                        if (cell.info.header === "flags") {
                          return (
                            <TableCell key={cell.id}>
                              {src.shadow_mode && <Tag type="cyan">shadow</Tag>}
                              {src.kill_switch && <Tag type="red">kill</Tag>}
                            </TableCell>
                          );
                        }
                        if (cell.info.header === "actions") {
                          return (
                            <TableCell key={cell.id}>
                              <div style={{ display: "flex", gap: "0.25rem" }}>
                                <Button
                                  kind="primary"
                                  size="sm"
                                  onClick={() => promote.mutate(row.id as string)}
                                >
                                  Promote
                                </Button>
                                <Button
                                  kind={src.shadow_mode ? "tertiary" : "ghost"}
                                  size="sm"
                                  onClick={() =>
                                    shadow.mutate({
                                      agent: row.id as string,
                                      engaged: !src.shadow_mode,
                                    })
                                  }
                                >
                                  Shadow
                                </Button>
                                <Button
                                  kind={src.kill_switch ? "danger" : "danger--tertiary"}
                                  size="sm"
                                  onClick={() =>
                                    kill.mutate({
                                      agent: row.id as string,
                                      engaged: !src.kill_switch,
                                    })
                                  }
                                >
                                  Kill
                                </Button>
                              </div>
                            </TableCell>
                          );
                        }
                        return <TableCell key={cell.id}>{cell.value}</TableCell>;
                      })}
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </DataTable>
      </Section>

      <Section title="Audit log">
        {audit.isLoading || !audit.data ? (
          <SkeletonText paragraph />
        ) : (
          <Tile style={{ padding: "1rem", maxHeight: 400, overflow: "auto" }}>
            <pre className="optico-evidence">
              {(audit.data as any[]).slice(0, 100).map((e, i) => JSON.stringify(e)).join("\n")}
            </pre>
          </Tile>
        )}
      </Section>
    </div>
  );
}
