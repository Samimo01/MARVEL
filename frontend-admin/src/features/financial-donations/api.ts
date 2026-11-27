import { apiRequest } from "@/app/api-client";
import type { FinancialDonation } from "@/features/financial-donations/types";
export const listFinancialDonations = (filters?: { status?: string }) =>
  apiRequest<FinancialDonation[]>("/dons", { query: filters });
export const getFinancialDonation = (id: string) =>
  apiRequest<FinancialDonation>(`/dons/${id}`);
export const getSuccessfulDonations = () =>
  apiRequest<FinancialDonation[]>("/dons/succeed");
export const generateDonationReceipt = (id: string) =>
  apiRequest<{ receipt_url: string; message: string }>(`/dons/${id}/receipt`, {
    method: "POST",
  });
