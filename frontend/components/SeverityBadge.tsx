interface SeverityBadgeProps {
  severity: string;
}

const MAP: Record<string, { label: string; cls: string }> = {
  none:   { label: "Healthy",  cls: "badge-none" },
  low:    { label: "Low",      cls: "badge-low" },
  LOW:    { label: "LOW",      cls: "badge-low" },
  medium: { label: "Medium",   cls: "badge-medium" },
  moderate: { label: "MODERATE", cls: "badge-medium" },
  MODERATE: { label: "MODERATE", cls: "badge-medium" },
  high:   { label: "High ⚠️",  cls: "badge-high" },
  HIGH:   { label: "HIGH ⚠️",  cls: "badge-high" },
  critical: { label: "CRITICAL", cls: "badge-high" },
  CRITICAL: { label: "CRITICAL", cls: "badge-high" },
};

export default function SeverityBadge({ severity }: SeverityBadgeProps) {
  const entry = MAP[severity] ?? { label: severity, cls: "badge-low" };
  return <span className={entry.cls}>{entry.label}</span>;
}
