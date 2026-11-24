import { NavLink } from 'react-router-dom'

import { ArrowRightIcon } from '@/components/icons/index.tsx'
import { focusRing } from '@/components/layout/classes.ts'
import JoinButton from '@/components/layout/JoinButton.tsx'
import type { NavItem } from '@/components/layout/types.ts'

type MobileMenuProps = {
  open: boolean
  items: NavItem[]
  isAuthenticated: boolean
  onLogout: () => void
  logoutPending: boolean
  onNavigate: () => void
}

// Classes statiques (Tailwind ne détecte pas les classes construites dynamiquement).
const staggerDelays = ['delay-75', 'delay-100', 'delay-150', 'delay-200', 'delay-300']

export default function MobileMenu({
  open,
  items,
  isAuthenticated,
  onLogout,
  logoutPending,
  onNavigate,
}: MobileMenuProps) {
  const itemMotion = (index: number) =>
    open
      ? `translate-y-0 opacity-100 ${staggerDelays[index] ?? 'delay-300'}`
      : '-translate-y-2 opacity-0'

  return (
    <div className="absolute inset-x-0 top-full px-3 sm:px-4 lg:hidden">
      {/* `inert` retire le menu fermé de l'ordre de tabulation et de l'arbre d'accessibilité. */}
      <div
        id="mobile-menu"
        inert={!open}
        className={`mx-auto grid w-full max-w-md transition-[grid-template-rows,opacity] duration-300 ease-out motion-reduce:transition-none ${
          open ? 'grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0'
        }`}
      >
        <div className="overflow-hidden">
          <nav
            aria-label="Navigation principale mobile"
            className="flex flex-col gap-1.5 rounded-3xl border border-foreground/10 bg-foreground/10 p-3 shadow-[0_8px_24px_rgba(0,0,0,.08)] ring-1 ring-inset ring-foreground/5 backdrop-blur-xl"
          >
            {items.map((item, index) => (
              <NavLink
                key={item.to}
                to={item.to}
                end
                onClick={onNavigate}
                className={({ isActive }) =>
                  `group flex items-center justify-between rounded-2xl px-4 py-3.5 font-semibold transition duration-300 hover:bg-foreground/5 hover:text-foreground motion-reduce:transition-none ${focusRing} ${
                    isActive ? 'bg-foreground/10 text-foreground' : 'text-muted'
                  } ${itemMotion(index)}`
                }
              >
                {({ isActive }) => (
                  <>
                    <span className="flex items-center gap-3">
                      <span
                        aria-hidden="true"
                        className={`h-1.5 w-1.5 rounded-full transition-colors duration-200 ${
                          isActive ? 'bg-primary' : 'bg-transparent'
                        }`}
                      />
                      {item.label}
                    </span>
                    <ArrowRightIcon className="h-4 w-4 text-primary opacity-0 transition duration-200 group-hover:translate-x-1 group-hover:opacity-100" />
                  </>
                )}
              </NavLink>
            ))}

            <div aria-hidden="true" className="my-1 h-px bg-border/60" />

            {isAuthenticated ? (
              <button
                type="button"
                className={`min-h-12 rounded-2xl border border-danger/30 bg-danger/5 px-4 py-3 font-semibold text-danger transition duration-300 hover:bg-danger/15 disabled:cursor-not-allowed disabled:opacity-50 motion-reduce:transition-none ${focusRing} ${itemMotion(items.length)}`}
                onClick={onLogout}
                disabled={logoutPending}
              >
                {logoutPending ? 'Déconnexion...' : 'Déconnexion'}
              </button>
            ) : (
              <JoinButton compact onClick={onNavigate} />
            )}
          </nav>
        </div>
      </div>
    </div>
  )
}