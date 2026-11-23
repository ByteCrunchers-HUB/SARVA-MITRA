import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import type { FarmConfig } from "@/api/types";
import {
  DEFAULT_FARM,
  loadFarm,
  saveFarm,
} from "@/store/farm";

export const FARM_QUERY_KEY = ["farm"] as const;

export function useFarmConfig() {
  const query = useQuery({
    queryKey: FARM_QUERY_KEY,
    queryFn: loadFarm,
    staleTime: Infinity,
  });

  return {
    farm: query.data ?? DEFAULT_FARM,
    isLoading: query.isLoading,
    isError: query.isError,
    refetch: query.refetch,
  };
}

export function useSaveFarm() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (farm: FarmConfig) => saveFarm(farm),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: FARM_QUERY_KEY });
      await queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      await queryClient.invalidateQueries({ queryKey: ["riskTrend"] });
    },
  });
}
