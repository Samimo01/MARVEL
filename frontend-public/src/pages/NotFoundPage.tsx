import { Link } from 'react-router-dom'

import PublicLayout from './PublicLayout.tsx'

export default function NotFoundPage() {
  return (
    <PublicLayout>
      <h1 className="mb-4 text-3xl font-bold">Page introuvable</h1>
      <Link to="/" className="font-medium underline">
        Retour à l'accueil
      </Link>
    </PublicLayout>
  )
}
