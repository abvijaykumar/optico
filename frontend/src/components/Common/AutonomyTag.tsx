import { Tag } from "@carbon/react";

const LABELS = [
  "L0 Recommend",
  "L1 One-click",
  "L2 Review",
  "L3 Notify",
  "L4 Autonomous",
];

const TYPES = ["cool-gray", "blue", "teal", "green", "magenta"] as const;

export function AutonomyTag({ level }: { level: number }) {
  const safe = Math.max(0, Math.min(4, Math.round(level)));
  return (
    <Tag type={TYPES[safe]} size="sm">
      {LABELS[safe]}
    </Tag>
  );
}
