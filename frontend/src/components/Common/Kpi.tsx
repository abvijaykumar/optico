export function KpiCard({
  label,
  value,
  hint,
}: {
  label: string;
  value: string | number;
  hint?: string;
}) {
  return (
    <div className="optico-kpi-card">
      <div className="optico-kpi-card__label">{label}</div>
      <div className="optico-kpi-card__value">{value}</div>
      {hint && (
        <div style={{ fontSize: "0.75rem", color: "var(--cds-text-secondary)" }}>
          {hint}
        </div>
      )}
    </div>
  );
}
