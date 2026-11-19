import { useAsync } from '@/hooks/useAsync.ts'
import { fetchPublicCampaigns } from '@/features/campaigns/api.ts'

export function useCampaigns() {
  return useAsync(fetchPublicCampaigns)
}
