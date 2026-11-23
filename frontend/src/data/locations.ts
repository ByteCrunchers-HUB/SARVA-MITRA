import type { Crop } from "@/api/types";

export type LocationPreset = {
  name: string;
  lat: number;
  lon: number;
};

export const LOCATION_PRESETS: LocationPreset[] = [
  { name: "Kakinada, AP", lat: 16.98, lon: 82.24 },
  { name: "Vijayawada, AP", lat: 16.51, lon: 80.52 },
  { name: "Bengaluru, KA", lat: 12.97, lon: 77.59 },
  { name: "Hyderabad, TS", lat: 17.38, lon: 78.49 },
  { name: "Chennai, TN", lat: 13.08, lon: 80.27 },
  { name: "Nagpur, MH", lat: 21.15, lon: 79.09 },
  { name: "Bhubaneswar, OD", lat: 20.3, lon: 85.82 },
  { name: "Lucknow, UP", lat: 26.85, lon: 80.95 },
  { name: "Jaipur, RJ", lat: 26.91, lon: 75.79 },
  { name: "Kolkata, WB", lat: 22.57, lon: 88.36 },
  { name: "Patna, BR", lat: 25.59, lon: 85.14 },
];

export const CROP_OPTIONS: { id: Crop; label: string }[] = [
  { id: "tomato", label: "Tomato" },
  { id: "chilli", label: "Chilli" },
  { id: "ragi", label: "Ragi" },
];

export const STAGE_OPTIONS = [
  { id: "seedling", label: "Seedling" },
  { id: "vegetative", label: "Vegetative" },
  { id: "flowering", label: "Flowering" },
  { id: "maturity", label: "Maturity" },
];
