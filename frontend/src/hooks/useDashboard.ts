import { useQuery } from "@tanstack/react-query";

import { getDashboard } from "@/api/client";
import type { FarmConfig } from "@/api/types";
import { farmHash } from "@/store/farm";

export function useDashboard(farm: FarmConfig) {
  return useQuery({
    queryKey: ["dashboard", farmHash(farm)],
    queryFn: () => getDashboard(farm),
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}
