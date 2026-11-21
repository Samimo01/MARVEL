import type { ReactNode } from 'react'

import Footer from '@/components/layout/Footer.tsx'
import Header, { type NavItem } from '@/components/layout/Header.tsx'
import PageContainer from '@/components/layout/PageContainer.tsx'

type AppLayoutProps = {
  title: string
  navItems: NavItem[]
  footerText: string
  children: ReactNode
  isAuthenticated?: boolean
  onLogout?: () => void
  logoutPending?: boolean
}

/** Squelette commun des pages : en-tête, contenu, pied de page. Textes passés en props. */
export default function AppLayout({
  title,
  navItems,
  footerText,
  children,
  isAuthenticated,
  onLogout,
  logoutPending,
}: AppLayoutProps) {
  return (
    <div className="flex min-h-screen flex-col">
      <Header
        title={title}
        items={navItems}
        isAuthenticated={isAuthenticated}
        onLogout={onLogout}
        logoutPending={logoutPending}
      />
      <PageContainer>{children}</PageContainer>
      <Footer text={footerText} />
    </div>
  )
}
