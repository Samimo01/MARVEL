export type Budget = {
  total_donations: number | string;
  total_income: number | string;
  total_expenses: number | string;
  balance: number | string;
};
export type Fund = {
  id_fund: string;
  amount: number | string;
  category?: string | null;
  transaction_at: string;
  justificative?: string | null;
  id_event?: string | null;
};
