import { useAsync } from '../../../hooks/useAsync.ts'
import { fetchPublicCampaigns } from '../api.ts'

export function useCampaigns() {
  return useAsync(fetchPublicCampaigns)
}
