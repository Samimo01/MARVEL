import { apiRequest } from "@/app/api-client";
import type {
  NaturalDonation,
  NaturalDonationDetail,
} from "@/features/natural-donations/types";
export const listNaturalDonations = (status?: string) =>
  apiRequest<NaturalDonation[]>("/donations/natural", { query: { status } });
export const getNaturalDonation = (id: string) =>
  apiRequest<NaturalDonationDetail>(`/donations/natural/${id}`);
export const validateNaturalDonation = (id: string) =>
  apiRequest<NaturalDonation>(`/donations/natural/${id}/validate`, {
    method: "POST",
  });
export const rejectNaturalDonation = (id: string, refusal_reason: string) =>
  apiRequest<NaturalDonation>(`/donations/natural/${id}/reject`, {
    method: "POST",
    body: { refusal_reason },
  });
export const planNaturalCollection = (
  id: string,
  payload: { planned_at: string; collection_address: string },
) =>
  apiRequest<NaturalDonation>(`/donations/natural/${id}/collects`, {
    method: "POST",
    body: payload,
  });
export const stockInNaturalDonation = (id: string) =>
  apiRequest<NaturalDonationDetail>(`/donations/natural/${id}/stock-in`, {
    method: "POST",
  });
