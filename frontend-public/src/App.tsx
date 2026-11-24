import { Navigate, Route, Routes } from 'react-router-dom'

import CampaignsPage from '@/pages/CampaignsPage.tsx'
import HomePage from '@/pages/HomePage.tsx'
import NotFoundPage from '@/pages/NotFoundPage.tsx'
import AuthPage from '@/pages/AuthPage.tsx'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/campagnes" element={<CampaignsPage />} />
      <Route path="/auth" element={<AuthPage />} />
      <Route path="/inscription" element={<Navigate to="/auth?mode=register" replace />} />
      <Route path="/connexion" element={<Navigate to="/auth?mode=login" replace />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}
