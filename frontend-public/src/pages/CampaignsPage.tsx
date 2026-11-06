import CampaignList from '../features/campaigns/components/CampaignList.tsx'
import PublicLayout from './PublicLayout.tsx'

export default function CampaignsPage() {
  return (
    <PublicLayout>
      <h1 className="mb-6 text-3xl font-bold">Campagnes en cours</h1>
      <CampaignList />
    </PublicLayout>
  )
}
