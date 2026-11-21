import type { ReactNode } from 'react'

import AppLayout from '@/components/layout/AppLayout.tsx'
import { PUBLIC_FOOTER_TEXT } from '@/components/layout/Footer.tsx'
import { publicNavigationItems } from '@/components/layout/navigation-items.ts'
import useHeaderAuthActions from '@/features/auth/useHeaderAuthActions.ts'

export default function PublicLayout({ children }: { children: ReactNode }) {
  const { isAuthenticated, logoutPending, handleLogout } = useHeaderAuthActions()

  return (
    <AppLayout
      title="MARVEL"
      navItems={publicNavigationItems}
      footerText={PUBLIC_FOOTER_TEXT}
      isAuthenticated={isAuthenticated}
      onLogout={handleLogout}
      logoutPending={logoutPending}
    >
      {children}
    </AppLayout>
  )
}
