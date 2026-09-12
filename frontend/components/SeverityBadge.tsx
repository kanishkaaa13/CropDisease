interface SeverityBadgeProps {
  severity: string;
}

const MAP: Record<string, { label: string; cls: string }> = {
  none:   { label: "Healthy",  cls: "badge-none" },
  low:    { label: "Low",      cls: "badge-low" },
  medium: { label: "Medium",   cls: "badge-medium" },
  high:   { label: "High ⚠️",  cls: "badge-high" },
};

export default function SeverityBadge({ severity }: SeverityBadgeProps) {
  const entry = MAP[severity] ?? { label: severity, cls: "badge-low" };
  return <span className={entry.cls}>{entry.label}</span>;
}
