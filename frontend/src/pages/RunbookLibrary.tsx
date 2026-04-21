import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Heading,
  SkeletonText,
  Tile,
  Tag,
  Accordion,
  AccordionItem,
  Search,
  Tabs,
  Tab,
  TabList,
  TabPanels,
  TabPanel,
} from "@carbon/react";

import { api } from "@/api/client";

export default function RunbookLibrary() {
  const [q, setQ] = useState("");
  const runbooks = useQuery({ queryKey: ["runbooks"], queryFn: api.listRunbooks });
  const kedb = useQuery({ queryKey: ["kedb", q], queryFn: () => api.listKEDB(q) });

  return (
    <div>
      <Heading>Runbooks & KEDB</Heading>
      <p style={{ color: "var(--cds-text-secondary)" }}>
        Authored by humans, augmented by agents.
      </p>
      <Tabs>
        <TabList>
          <Tab>Runbooks</Tab>
          <Tab>Known Errors (KEDB)</Tab>
        </TabList>
        <TabPanels>
          <TabPanel>
            {runbooks.isLoading || !runbooks.data ? (
              <SkeletonText paragraph lineCount={3} />
            ) : (
              <Accordion>
                {(runbooks.data as any[]).map((rb: any) => (
                  <AccordionItem
                    key={rb.id}
                    title={
                      <span>
                        <strong>{rb.title}</strong>{" "}
                        <Tag size="sm" type="cool-gray">{rb.service}</Tag>{" "}
                        <Tag size="sm" type="green">
                          {Math.round((rb.success_rate ?? 0) * 100)}% success
                        </Tag>
                      </span>
                    }
                  >
                    <ol>
                      {(rb.steps || []).map((s: any) => (
                        <li key={s.n}>{s.do}</li>
                      ))}
                    </ol>
                  </AccordionItem>
                ))}
              </Accordion>
            )}
          </TabPanel>
          <TabPanel>
            <Search
              id="kedb-search"
              labelText="Search KEDB"
              placeholder="symptom or title"
              value={q}
              onChange={(e) => setQ((e.target as HTMLInputElement).value)}
            />
            {kedb.isLoading || !kedb.data ? (
              <SkeletonText paragraph />
            ) : (
              (kedb.data as any[]).map((e: any) => (
                <Tile key={e.id} style={{ marginTop: "0.5rem", padding: "1rem" }}>
                  <strong>{e.title}</strong> <Tag size="sm">{e.id}</Tag>
                  <div>
                    <em>Symptoms:</em> {(e.symptoms || []).join(", ")}
                  </div>
                  <div>
                    <em>Root cause:</em> {e.root_cause}
                  </div>
                  <div>
                    <em>Workaround:</em> {e.workaround}
                  </div>
                </Tile>
              ))
            )}
          </TabPanel>
        </TabPanels>
      </Tabs>
    </div>
  );
}
