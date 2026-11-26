import { apiRequest, apiDownload } from "@/app/api-client";
import type { Budget, Fund } from "@/features/treasury/types";
export const getBudgetSummary = () => apiRequest<Budget>("/treasury/budget");
export const listFunds = () => apiRequest<Fund[]>("/funds");
export const getFund = (id: string) => apiRequest<Fund>(`/funds/${id}`);
export const listExpenses = (eventId: string) =>
  apiRequest<Fund[]>(`/funds/${eventId}/expenses`);
export const createExpense = (eventId: string, payload: FormData) =>
  apiRequest<Fund>(`/funds/${eventId}/expenses`, {
    method: "POST",
    body: payload,
  });
export const exportTreasury = (format: "csv" | "xlsx" | "pdf") =>
  apiDownload("/treasury/export", `rapport-tresorerie.${format}`, { format });
