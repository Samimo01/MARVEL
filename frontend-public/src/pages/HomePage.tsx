import { Link } from 'react-router-dom'

import CampaignList from '@/features/campaigns/components/CampaignList.tsx'
import PublicLayout from '@/pages/PublicLayout.tsx'

export default function HomePage() {
  return (
    <PublicLayout>
      <section className="mb-10">
        <h1 className="mb-2 max-w-3xl text-5xl font-black leading-tight">
          Rejoignez le mouvement pour <span className="text-[#ff6b4a]">donner.</span>
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
