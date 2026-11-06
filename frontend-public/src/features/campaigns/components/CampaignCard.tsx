import Card from '../../../components/ui/Card.tsx'
import ProgressBar from '../../../components/ui/ProgressBar.tsx'
import { formatAmount } from '../../../lib/format.ts'
import type { Campaign } from '../types.ts'

export default function CampaignCard({ campaign }: { campaign: Campaign }) {
  const collected = Number(campaign.collected_amount)
  const goal = Number(campaign.goal_amount)

  return (
    <Card className="flex flex-col gap-3">
      <h3 className="text-lg font-semibold">{campaign.title}</h3>
      <p className="text-muted">{campaign.description}</p>
      <ProgressBar value={collected} max={goal} label={campaign.title} />
      <p className="text-sm">
        {formatAmount(collected)} collectés sur {formatAmount(goal)}
      </p>
    </Card>
  )
}
