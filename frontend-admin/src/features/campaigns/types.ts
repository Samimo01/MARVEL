export type Campaign = {
  id_campaign: string;
  title: string;
  description?: string | null;
  goal?: number | string | null;
  status: string;
  start_at?: string | null;
  finish_at?: string | null;
  created_at?: string;
  collected_amount?: number | string;
};
