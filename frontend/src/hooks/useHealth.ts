import { useQuery } from "@tanstack/react-query";

import { getHealth } from "@/api/client";

export function useHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: getHealth,
    staleTime: 2 * 60 * 1000,
    retry: 0,
  });
}
