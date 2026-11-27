import { useAsyncResource } from "@/hooks/use-async-resource";
import { listBeneficiaries } from "@/features/beneficiaries/api";
export function useBeneficiaries() {
  return useAsyncResource(listBeneficiaries);
}
