import { apiRequest } from "@/app/api-client";
import type { Mission } from "@/features/missions/types";
export const listMissions = () => apiRequest<Mission[]>("/missions");
export const createMission = (payload: Partial<Mission>) =>
  apiRequest<Mission>("/missions", { method: "POST", body: payload });
export const updateMission = (id: string, payload: Partial<Mission>) =>
  apiRequest<Mission>(`/missions/${id}`, { method: "PUT", body: payload });
export const publishMission = (id: string) =>
  apiRequest<Mission>(`/missions/${id}/publish`, { method: "POST" });
export const completeMission = (id: string) =>
  apiRequest<Mission>(`/missions/${id}/complete`, { method: "POST" });
export const cancelMission = (id: string) =>
  apiRequest<Mission>(`/missions/${id}/cancel`, { method: "POST" });
export const deleteMission = (id: string) =>
  apiRequest<void>(`/missions/${id}`, { method: "DELETE" });
