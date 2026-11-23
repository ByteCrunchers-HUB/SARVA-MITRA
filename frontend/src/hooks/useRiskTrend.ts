import { useQuery } from "@tanstack/react-query";

import { getRiskTrend } from "@/api/riskTrend";
import type { FarmConfig } from "@/api/types";
import { farmHash } from "@/store/farm";

export function useRiskTrend(farm: FarmConfig) {
  return useQuery({
    queryKey: ["riskTrend", farmHash(farm)],
    queryFn: () => getRiskTrend(farm),
    staleTime: 6 * 60 * 60 * 1000,
    retry: 1,
  });
}
