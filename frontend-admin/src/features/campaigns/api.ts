import { apiRequest } from "@/app/api-client";
import type { Campaign } from "@/features/campaigns/types";
export const listCampaigns = () => apiRequest<Campaign[]>("/campaigns");
export const getCampaign = (id: string) =>
  apiRequest<Campaign>(`/campaigns/${id}`);
export const createCampaign = (payload: Partial<Campaign>) =>
  apiRequest<Campaign>("/campaigns", { method: "POST", body: payload });
export const updateCampaign = (id: string, payload: Partial<Campaign>) =>
  apiRequest<Campaign>(`/campaigns/${id}`, { method: "PUT", body: payload });
export const publishCampaign = (id: string) =>
  apiRequest<Campaign>(`/campaigns/${id}/publish`, { method: "POST" });
export const closeCampaign = (id: string) =>
  apiRequest<Campaign>(`/campaigns/${id}/close`, { method: "POST" });
export const deactivateCampaign = (id: string) =>
  apiRequest<Campaign>(`/campaigns/${id}/deactivate`, { method: "POST" });
export const deleteCampaign = (id: string) =>
  apiRequest<void>(`/campaigns/${id}`, { method: "DELETE" });
