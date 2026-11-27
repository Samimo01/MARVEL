export type NaturalDonation = {
  id_don_n: string;
  status: string;
  recovery_mode?: string | null;
  collection_address?: string | null;
  created_at: string;
  id_campaign?: string | null;
  id_collect?: string | null;
};
export type NaturalDonationDetail = NaturalDonation & {
  items: {
    id_nat: string;
    description?: string | null;
    declared_quantity?: number | string | null;
    received_quantity?: number | string | null;
    is_compliant?: boolean | null;
    image_url?: string | null;
  }[];
};
