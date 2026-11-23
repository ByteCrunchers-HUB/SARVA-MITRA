import type { FarmConfig } from "@/api/types";

/**
 * Snapshot of backend/ml_engine/models/static_features.csv.
 * These are reference soil properties for the nearest trained grid point,
 * not a live soil lab test. The ML engine snaps coordinates the same way.
 */
export type SoilReference = {
  lat: number;
  lon: number;
  soil_ph: number;
  organic_carbon: number;
  clay_pct: number;
  sand_pct: number;
  silt_pct: number;
  elevation_m: number;
};

export const SOIL_REFERENCE_POINTS: SoilReference[] = [
  { lat: 8.52, lon: 76.94, soil_ph: 5.8, organic_carbon: 18.0, clay_pct: 32.0, sand_pct: 40.0, silt_pct: 28.0, elevation_m: 26.0 },
  { lat: 12.97, lon: 77.59, soil_ph: 6.4, organic_carbon: 27.6, clay_pct: 24.6, sand_pct: 53.6, silt_pct: 21.9, elevation_m: 914.0 },
  { lat: 13.08, lon: 80.27, soil_ph: 6.5, organic_carbon: 8.0, clay_pct: 38.0, sand_pct: 34.0, silt_pct: 28.0, elevation_m: 10.0 },
  { lat: 15.49, lon: 73.83, soil_ph: 6.0, organic_carbon: 12.0, clay_pct: 28.0, sand_pct: 52.0, silt_pct: 20.0, elevation_m: 6.0 },
  { lat: 16.51, lon: 80.52, soil_ph: 7.0, organic_carbon: 16.3, clay_pct: 29.7, sand_pct: 36.1, silt_pct: 34.2, elevation_m: 21.0 },
  { lat: 17.39, lon: 78.49, soil_ph: 6.9, organic_carbon: 8.5, clay_pct: 38.0, sand_pct: 33.0, silt_pct: 29.0, elevation_m: 502.0 },
  { lat: 20.3, lon: 85.82, soil_ph: 6.2, organic_carbon: 21.8, clay_pct: 30.1, sand_pct: 38.7, silt_pct: 31.3, elevation_m: 54.0 },
  { lat: 21.15, lon: 79.09, soil_ph: 7.2, organic_carbon: 7.5, clay_pct: 42.0, sand_pct: 30.0, silt_pct: 28.0, elevation_m: 310.0 },
  { lat: 21.25, lon: 81.63, soil_ph: 6.4, organic_carbon: 9.0, clay_pct: 25.0, sand_pct: 50.0, silt_pct: 25.0, elevation_m: 297.0 },
  { lat: 22.57, lon: 88.36, soil_ph: 6.0, organic_carbon: 12.5, clay_pct: 30.0, sand_pct: 38.0, silt_pct: 32.0, elevation_m: 12.0 },
  { lat: 23.22, lon: 72.65, soil_ph: 7.4, organic_carbon: 9.4, clay_pct: 32.0, sand_pct: 32.3, silt_pct: 35.7, elevation_m: 77.0 },
  { lat: 23.26, lon: 77.41, soil_ph: 7.0, organic_carbon: 7.0, clay_pct: 35.0, sand_pct: 38.0, silt_pct: 27.0, elevation_m: 501.0 },
  { lat: 23.34, lon: 85.31, soil_ph: 5.8, organic_carbon: 11.0, clay_pct: 28.0, sand_pct: 48.0, silt_pct: 24.0, elevation_m: 650.0 },
  { lat: 23.73, lon: 92.72, soil_ph: 5.5, organic_carbon: 22.0, clay_pct: 28.0, sand_pct: 44.0, silt_pct: 28.0, elevation_m: 973.0 },
  { lat: 23.83, lon: 91.28, soil_ph: 5.8, organic_carbon: 14.0, clay_pct: 28.0, sand_pct: 43.0, silt_pct: 29.0, elevation_m: 12.0 },
  { lat: 24.82, lon: 93.94, soil_ph: 5.7, organic_carbon: 20.0, clay_pct: 28.0, sand_pct: 42.0, silt_pct: 30.0, elevation_m: 782.0 },
  { lat: 25.57, lon: 91.88, soil_ph: 5.4, organic_carbon: 25.0, clay_pct: 26.0, sand_pct: 45.0, silt_pct: 29.0, elevation_m: 1513.0 },
  { lat: 25.61, lon: 85.14, soil_ph: 7.2, organic_carbon: 7.5, clay_pct: 30.0, sand_pct: 38.0, silt_pct: 32.0, elevation_m: 56.0 },
  { lat: 25.67, lon: 94.11, soil_ph: 5.6, organic_carbon: 21.0, clay_pct: 27.0, sand_pct: 43.0, silt_pct: 30.0, elevation_m: 1448.0 },
  { lat: 26.14, lon: 91.79, soil_ph: 5.6, organic_carbon: 16.5, clay_pct: 28.0, sand_pct: 38.0, silt_pct: 34.0, elevation_m: 56.0 },
  { lat: 26.85, lon: 80.95, soil_ph: 7.4, organic_carbon: 6.5, clay_pct: 22.0, sand_pct: 55.0, silt_pct: 23.0, elevation_m: 117.0 },
  { lat: 26.91, lon: 75.79, soil_ph: 7.9, organic_carbon: 3.5, clay_pct: 14.0, sand_pct: 70.0, silt_pct: 16.0, elevation_m: 430.0 },
  { lat: 27.08, lon: 93.61, soil_ph: 5.1, organic_carbon: 30.4, clay_pct: 26.6, sand_pct: 38.9, silt_pct: 34.5, elevation_m: 220.0 },
  { lat: 27.33, lon: 88.61, soil_ph: 5.7, organic_carbon: 54.6, clay_pct: 26.7, sand_pct: 36.2, silt_pct: 37.1, elevation_m: 1551.0 },
  { lat: 29.15, lon: 75.72, soil_ph: 7.8, organic_carbon: 4.5, clay_pct: 18.0, sand_pct: 62.0, silt_pct: 20.0, elevation_m: 212.0 },
  { lat: 30.32, lon: 78.03, soil_ph: 6.3, organic_carbon: 16.0, clay_pct: 26.0, sand_pct: 46.0, silt_pct: 28.0, elevation_m: 656.0 },
  { lat: 30.9, lon: 75.85, soil_ph: 7.6, organic_carbon: 5.0, clay_pct: 17.0, sand_pct: 63.0, silt_pct: 20.0, elevation_m: 250.0 },
  { lat: 31.1, lon: 77.17, soil_ph: 6.0, organic_carbon: 52.9, clay_pct: 25.4, sand_pct: 36.4, silt_pct: 38.2, elevation_m: 1940.0 },
];

export function nearestSoilReference(lat: number, lon: number): SoilReference {
  let best = SOIL_REFERENCE_POINTS[0];
  let bestDistance = Number.POSITIVE_INFINITY;

  for (const point of SOIL_REFERENCE_POINTS) {
    const dLat = point.lat - lat;
    const dLon = point.lon - lon;
    const distance = dLat * dLat + dLon * dLon;
    if (distance < bestDistance) {
      best = point;
      bestDistance = distance;
    }
  }

  return best;
}

export function soilReferenceForFarm(farm: FarmConfig): SoilReference {
  return nearestSoilReference(farm.lat, farm.lon);
}
