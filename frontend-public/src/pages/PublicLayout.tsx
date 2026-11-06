import type { ReactNode } from 'react'

import AppLayout from '../components/layout/AppLayout.tsx'

const navItems = [
  { to: '/', label: 'Accueil' },
  { to: '/campagnes', label: 'Campagnes' },
]

export default function PublicLayout({ children }: { children: ReactNode }) {
  return (
    <AppLayout
      title="Association caritative"
      navItems={navItems}
      footerText="© Association caritative — Projet DevOps"
    >
      {children}
    </AppLayout>
  )
}
