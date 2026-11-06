import { Link } from 'react-router-dom'

import CampaignList from '../features/campaigns/components/CampaignList.tsx'
import PublicLayout from './PublicLayout.tsx'

export default function HomePage() {
  return (
    <PublicLayout>
      <section className="mb-10">
        <h1 className="mb-2 text-3xl font-bold">
          Ensemble, aidons ceux qui en ont besoin
        </h1>
        <p className="mb-4 max-w-2xl text-muted">
          Chaque don est tracé, du reçu à la distribution. Consultez nos campagnes en cours.
        </p>
        <Link to="/campagnes" className="font-medium underline">
          Voir les campagnes
        </Link>
      </section>

      <section aria-labelledby="campaigns-heading">
        <h2 id="campaigns-heading" className="mb-4 text-2xl font-semibold">
          Campagnes en cours
        </h2>
        <CampaignList />
      </section>
    </PublicLayout>
  )
}
