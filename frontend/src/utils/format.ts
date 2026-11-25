import { colors } from "@/theme";
import type { RiskLevel } from "@/api/types";

export function formatNumber(
  value: number | null | undefined,
  digits = 0,
): string {
  if (value == null || Number.isNaN(value)) return "—";
  return value.toFixed(digits);
}

export function formatRelativeTime(iso?: string): string {
  if (!iso) return "just now";
  const timestamp = Date.parse(iso);
  if (Number.isNaN(timestamp)) return "just now";
  const minutes = Math.max(0, Math.round((Date.now() - timestamp) / 60_000));
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours} hr ago`;
  const days = Math.round(hours / 24);
  return `${days} day${days === 1 ? "" : "s"} ago`;
}

export function riskLabel(level?: RiskLevel | string): string {
  if (level === "high") return "High";
  if (level === "moderate") return "Moderate";
  return "Low";
}

export function riskColor(level?: RiskLevel | string): string {
  if (level === "high") return colors.red;
  if (level === "moderate") return colors.amber;
  return colors.green;
}

export function riskSoftColor(level?: RiskLevel | string): string {
  if (level === "high") return colors.redSoft;
  if (level === "moderate") return colors.amberSoft;
  return colors.greenSoft;
}

export function deriveCondition(
  rainfallMm?: number | null,
  sunlightWm2?: number | null,
): string {
  if ((rainfallMm ?? 0) > 0.5) return "Rainy";
  if ((sunlightWm2 ?? 0) >= 600) return "Sunny";
  if ((sunlightWm2 ?? 0) >= 250) return "Partly cloudy";
  return "Cloudy";
}
