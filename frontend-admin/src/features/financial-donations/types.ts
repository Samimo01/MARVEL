export type FinancialDonation = {
  id_don_f: string;
  amount: number | string;
  status: string;
  created_at: string;
  paid_at?: string | null;
  is_anonymous: boolean;
  id_campaign: string;
};
