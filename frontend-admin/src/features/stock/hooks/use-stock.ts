import { useAsyncResource } from "@/hooks/use-async-resource";
import { listStockItems } from "@/features/stock/api";
export function useStock() {
  return useAsyncResource(listStockItems);
}
