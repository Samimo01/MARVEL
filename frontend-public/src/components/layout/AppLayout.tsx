import type { ReactNode } from 'react'

import Footer from './Footer.tsx'
import Header, { type NavItem } from './Header.tsx'
import PageContainer from './PageContainer.tsx'

type AppLayoutProps = {
  title: string
  navItems: NavItem[]
  footerText: string
  children: ReactNode
}

/** Squelette commun des pages : en-tête, contenu, pied de page. Textes passés en props. */
export default function AppLayout({
  title,
  navItems,
  footerText,
  children,
}: AppLayoutProps) {
  return (
    <div className="flex min-h-screen flex-col">
      <Header title={title} items={navItems} />
      <PageContainer>{children}</PageContainer>
      <Footer text={footerText} />
    </div>
  )
}
