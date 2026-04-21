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

export default function ToolVault() {
  const { data, isLoading } = useQuery({ queryKey: ["mcp-servers"], queryFn: api.listServers });

  if (isLoading || !data) return <SkeletonText paragraph lineCount={5} />;

  return (
    <div>
      <Heading>MCP Tool Vault</Heading>
      <p style={{ color: "var(--cds-text-secondary)" }}>
        Every registered MCP server and the tools agents may call through the policy-governed vault.
      </p>
      {(data as Array<any>).map((s) => (
        <Section
          key={s.name}
          title={s.name}
          action={<Tag type="purple">{s.tools.length} tools</Tag>}
        >
          <Tile style={{ padding: "1rem" }}>
            <p style={{ color: "var(--cds-text-secondary)" }}>{s.description}</p>
            <Accordion>
              {s.tools.map((t: any) => (
                <AccordionItem
                  key={t.qualified_name}
                  title={
                    <span>
                      <code>{t.qualified_name}</code>{" "}
                      {t.read_only ? (
                        <Tag type="green" size="sm">read-only</Tag>
                      ) : (
                        <Tag type="warm-gray" size="sm">min L{t.min_autonomy}</Tag>
                      )}
                    </span>
                  }
                >
                  <p>{t.description}</p>
                  <pre className="optico-evidence">{JSON.stringify(t.args_schema, null, 2)}</pre>
                </AccordionItem>
              ))}
            </Accordion>
          </Tile>
        </Section>
      ))}
    </div>
  );
}
