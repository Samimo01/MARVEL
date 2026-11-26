import { useAsyncResource } from "@/hooks/use-async-resource";
import { listReceipts } from "@/features/receipts/api";
export function useReceipts() {
  return useAsyncResource(listReceipts);
}
