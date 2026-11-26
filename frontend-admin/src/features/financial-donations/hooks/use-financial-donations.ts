import { useAsyncResource } from "@/hooks/use-async-resource";
import {
  generateDonationReceipt,
  listFinancialDonations,
} from "@/features/financial-donations/api";
export function useFinancialDonations() {
  const resource = useAsyncResource(listFinancialDonations);
  const rows = (resource.data ?? []).map((donation) => ({
    ...donation,
    canGenerateReceipt: ["success", "succeeded", "paid", "successful"].includes(
      donation.status.toLowerCase(),
    ),
  }));
  return { ...resource, rows, generateReceipt: generateDonationReceipt };
}
