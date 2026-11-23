import AsyncStorage from "@react-native-async-storage/async-storage";

import type { FarmConfig } from "@/api/types";

export const FARM_STORAGE_KEY = "sarva.farm.v1";

export const DEFAULT_FARM: FarmConfig = {
  name: "Farmer User",
  location: "Kakinada, AP",
  lat: 16.98,
  lon: 82.24,
  crop: "tomato",
  stage: "flowering",
};

export async function loadFarm(): Promise<FarmConfig> {
  try {
    const raw = await AsyncStorage.getItem(FARM_STORAGE_KEY);
    if (!raw) return DEFAULT_FARM;
    const parsed = JSON.parse(raw) as Partial<FarmConfig>;
    return { ...DEFAULT_FARM, ...parsed };
  } catch {
    return DEFAULT_FARM;
  }
}

export async function saveFarm(farm: FarmConfig): Promise<void> {
  await AsyncStorage.setItem(FARM_STORAGE_KEY, JSON.stringify(farm));
}

export function farmHash(farm: FarmConfig): string {
  return `${farm.lat.toFixed(2)}_${farm.lon.toFixed(2)}_${farm.crop}`;
}
