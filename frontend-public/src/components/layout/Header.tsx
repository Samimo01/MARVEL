import { useEffect, useState } from 'react'
import { NavLink } from 'react-router-dom'

import { LogoutIcon, MenuIcon } from '@/components/icons/index.tsx'
import JoinButton from '@/components/layout/JoinButton.tsx'
import { focusRing } from '@/components/layout/classes.ts'
import HeaderUtilities from '@/components/layout/HeaderUtilities.tsx'
import MobileMenu from '@/components/layout/MobileMenu.tsx'
import type { NavItem } from '@/components/layout/types.ts'

export type { NavItem } from '@/components/layout/types.ts'

type HeaderProps = {
  title: string
  items: NavItem[]
  isAuthenticated?: boolean
  onLogout?: () => void
  logoutPending?: boolean
}

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  `rounded-full px-3.5 py-2 text-sm font-semibold transition-colors duration-200 ${focusRing} ${
    isActive
      ? 'bg-foreground/10 text-foreground'
      : 'text-muted hover:bg-foreground/5 hover:text-foreground'
  }`

export default function Header({
  title,
  items,
  isAuthenticated = false,
  onLogout,
  logoutPending = false,
}: HeaderProps) {
  const [menuOpen, setMenuOpen] = useState(false)
  const [showMoonIcon, setShowMoonIcon] = useState(false)
  const toggleThemeIcon = () => setShowMoonIcon((showMoon) => !showMoon)

  useEffect(() => {
    if (!menuOpen) return
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') setMenuOpen(false)
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [menuOpen])

  const vIndex = title.indexOf('V')

  return (
    <header className="sticky top-0 z-40 px-3 py-3 sm:px-4 lg:px-6">
      <div className="mx-auto flex h-14 w-fit max-w-full items-center gap-5 rounded-full border border-foreground/10 bg-foreground/10 pl-5 pr-2 shadow-[0_4px_18px_rgba(0,0,0,.06)] ring-1 ring-inset ring-foreground/5 backdrop-blur-xl">
        <NavLink
          to="/"
          className={`rounded-md text-lg font-black tracking-[0.14em] text-foreground transition-opacity duration-200 hover:opacity-80 ${focusRing}`}
          aria-label="Retour à l'accueil"
        >
          {vIndex === -1 ? (
            title
          ) : (
            <>
              {title.slice(0, vIndex)}
              <span className="text-primary">V</span>
              {title.slice(vIndex + 1)}
            </>
          )}
        </NavLink>

        <div className="hidden items-center gap-4 lg:flex">
          <nav aria-label="Navigation principale" className="flex items-center gap-1">
            {items.map((item) => (
              <NavLink key={item.to} to={item.to} end className={navLinkClass}>
                {item.label}
              </NavLink>
            ))}
          </nav>

          <span aria-hidden="true" className="h-6 w-px bg-border/70" />

          <HeaderUtilities
            showMoon={showMoonIcon}
            onToggleThemeIcon={toggleThemeIcon}
          />

          {isAuthenticated ? (
            <button
              type="button"
              className={`inline-flex h-10 items-center gap-2 rounded-full border border-danger/30 bg-danger/5 px-4 text-sm font-semibold text-danger transition-colors duration-200 hover:bg-danger/15 disabled:cursor-not-allowed disabled:opacity-50 ${focusRing}`}
              onClick={onLogout}
              disabled={logoutPending}
            >
              <LogoutIcon className="h-4 w-4" />
              {logoutPending ? 'Déconnexion...' : 'Déconnexion'}
            </button>
          ) : (
            <JoinButton />
          )}
        </div>

        <div className="ml-auto flex items-center gap-2 lg:hidden">
          <HeaderUtilities
            showMoon={showMoonIcon}
            onToggleThemeIcon={toggleThemeIcon}
          />
          <button
            type="button"
            className={`inline-flex h-10 w-10 items-center justify-center rounded-full border border-border/60 bg-foreground/5 text-foreground transition-colors duration-200 hover:bg-foreground/10 ${focusRing}`}
            aria-label={menuOpen ? 'Fermer le menu' : 'Ouvrir le menu'}
            aria-expanded={menuOpen}
            aria-controls="mobile-menu"
            onClick={() => setMenuOpen((value) => !value)}
          >
            <MenuIcon open={menuOpen} />
          </button>
        </div>
      </div>

      <MobileMenu
        open={menuOpen}
        items={items}
        isAuthenticated={isAuthenticated}
        onLogout={() => {
          setMenuOpen(false)
          onLogout?.()
        }}
        logoutPending={logoutPending}
        onNavigate={() => setMenuOpen(false)}
      />
    </header>
  )
}