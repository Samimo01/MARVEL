import { apiRequest } from "@/app/api-client";
import type { Collect } from "@/features/collects/types";
import type { NaturalDonationDetail } from "@/features/natural-donations/types";
export const listCollects = () => apiRequest<Collect[]>("/collects");
export const updateCollect = (
  id: string,
  payload: { planned_at?: string; place?: string },
) => apiRequest<Collect>(`/collects/${id}`, { method: "PATCH", body: payload });
export const confirmCollect = (id: string) =>
  apiRequest<NaturalDonationDetail>(`/collects/${id}/confirm`, {
    method: "POST",
  });
