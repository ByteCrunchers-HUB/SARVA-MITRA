import { getTelemetryHistory, predictRisk } from "./client";
import type {
  FarmConfig,
  HistoricalRecord,
  RiskPoint,
} from "./types";

const DAY_MS = 24 * 60 * 60 * 1000;

function dayNumber(isoDate: string): number {
  return Math.floor(Date.parse(`${isoDate}T00:00:00Z`) / DAY_MS);
}

function isConsecutive(records: HistoricalRecord[]): boolean {
  if (records.length < 7) return false;
  for (let index = 1; index < records.length; index += 1) {
    if (
      dayNumber(records[index].date) - dayNumber(records[index - 1].date) !==
      1
    ) {
      return false;
    }
  }
  return true;
}

function toPredictionRecord(record: HistoricalRecord) {
  return {
    date: record.date,
    soil_moisture_pct: record.soil_moisture_pct,
    air_temperature_c: record.air_temperature_c,
    humidity_pct: record.humidity_pct,
    sunlight_wm2: record.sunlight_wm2,
    rainfall_mm: record.rainfall_mm,
  };
}

/**
 * Uses the existing ML endpoint to reconstruct risk for the last few days.
 * Each prediction uses only the seven days before its target date.
 */
export async function getRiskTrend(farm: FarmConfig): Promise<RiskPoint[]> {
  const records = await getTelemetryHistory(farm, 20);
  const sorted = [...records].sort((a, b) => a.date.localeCompare(b.date));
  const points: RiskPoint[] = [];

  for (let index = 7; index < sorted.length; index += 1) {
    const history = sorted.slice(index - 7, index);
    if (!isConsecutive(history)) continue;
    if (dayNumber(sorted[index].date) - dayNumber(sorted[index - 1].date) !== 1) {
      continue;
    }
    if (history.some((record) => record.sunlight_wm2 == null)) continue;

    const prediction = await predictRisk({
      device_id: "sarva-mitra-mobile",
      lat: farm.lat,
      lon: farm.lon,
      target_date: sorted[index].date,
      history: history.map(toPredictionRecord),
    });

    points.push({
      date: prediction.target_date,
      risk_pct: prediction.prediction.risk_pct,
      risk_level: prediction.prediction.risk_level,
    });
  }

  return points.slice(-7);
}
