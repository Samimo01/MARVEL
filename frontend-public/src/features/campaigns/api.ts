import { apiGet } from '../../lib/api-client.ts'
import type { Campaign } from './types.ts'

export function fetchPublicCampaigns(): Promise<Campaign[]> {
  return apiGet<Campaign[]>('/public/campaigns')
}
