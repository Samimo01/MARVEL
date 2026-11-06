import EmptyState from '../../../components/feedback/EmptyState.tsx'
import ErrorMessage from '../../../components/feedback/ErrorMessage.tsx'
import Spinner from '../../../components/feedback/Spinner.tsx'
import { useCampaigns } from '../hooks/useCampaigns.ts'
import CampaignCard from './CampaignCard.tsx'

/** Liste des campagnes publiques : prouve la communication front → API. */
export default function CampaignList() {
  const state = useCampaigns()

  if (state.status === 'loading') return <Spinner label="Chargement…" />
  if (state.status === 'error') {
    return (
      <ErrorMessage
        message="Impossible de contacter le serveur. Réessayez dans un instant."
        retryLabel="Réessayer"
        onRetry={state.reload}
      />
    )
  }
  if (state.data.length === 0) {
    return <EmptyState message="Aucune campagne en cours pour le moment." />
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2">
      {state.data.map((campaign) => (
        <CampaignCard key={campaign.id} campaign={campaign} />
      ))}
    </div>
  )
}
