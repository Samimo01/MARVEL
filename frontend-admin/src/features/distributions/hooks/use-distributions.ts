import { useAsyncResource } from "@/hooks/use-async-resource";
import { listDistributions } from "@/features/distributions/api";
export function useDistributions() {
  return useAsyncResource(listDistributions);
}
