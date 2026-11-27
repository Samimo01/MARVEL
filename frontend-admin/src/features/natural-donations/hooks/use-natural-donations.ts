import { useAsyncResource } from "@/hooks/use-async-resource";
import {
  listNaturalDonations,
  validateNaturalDonation,
  rejectNaturalDonation,
  stockInNaturalDonation,
} from "@/features/natural-donations/api";
const loadNaturalDonations = () => listNaturalDonations();
export function useNaturalDonations() {
  const resource = useAsyncResource(loadNaturalDonations);
  const rows = (resource.data ?? []).map((donation) => ({
    ...donation,
    canValidate: donation.status === "Declare",
    canReject: !["In_Stock", "Refuse"].includes(donation.status),
    canStockIn: ["valid", "Collection_Planned"].includes(donation.status),
  }));
  return {
    ...resource,
    rows,
    validate: async (id: string) => {
      await validateNaturalDonation(id);
      await resource.reload();
    },
    reject: async (id: string, reason: string) => {
      await rejectNaturalDonation(id, reason);
      await resource.reload();
    },
    stockIn: async (id: string) => {
      await stockInNaturalDonation(id);
      await resource.reload();
    },
  };
}
