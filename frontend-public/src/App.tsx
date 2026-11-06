import { Route, Routes } from 'react-router-dom'

import CampaignsPage from './pages/CampaignsPage.tsx'
import HomePage from './pages/HomePage.tsx'
import NotFoundPage from './pages/NotFoundPage.tsx'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/campagnes" element={<CampaignsPage />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}
