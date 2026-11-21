import type { ReactNode } from 'react'

import { HeartIcon, LockIcon, UsersIcon } from '@/components/icons/index.tsx'
import Footer, { PUBLIC_FOOTER_TEXT } from '@/components/layout/Footer.tsx'
import Header from '@/components/layout/Header.tsx'
import { publicNavigationItems } from '@/components/layout/navigation-items.ts'
import useHeaderAuthActions from '@/features/auth/useHeaderAuthActions.ts'

type AuthLayoutProps = {
  mode: 'login' | 'register'
  onModeChange?: (mode: 'login' | 'register') => void
  children: ReactNode
}

const highlights = [
  {
    label: 'Donner',
    tone: 'bg-primary text-primary-foreground',
    icon: <HeartIcon className="h-4 w-4" />,
  },
  {
    label: 'Demander une aide',
    tone: 'bg-champagne text-primary-foreground',
    icon: <LockIcon className="h-4 w-4" />,
  },
  {
    label: 'Proposer son aide',
    tone: 'bg-secondary text-white',
    icon: <UsersIcon className="h-4 w-4" />,
  },
]

const tabClass = (active: boolean) =>
  `relative z-10 flex min-h-12 items-center justify-center rounded-lg text-sm font-bold transition-colors duration-300 ${
    active ? 'text-surface' : 'text-muted hover:text-foreground'
  }`

export default function AuthLayout({ mode, onModeChange, children }: AuthLayoutProps) {
  const { isAuthenticated, logoutPending, handleLogout } = useHeaderAuthActions()
  const isRegister = mode === 'register'

  return (
    <main className="relative isolate flex min-h-screen flex-col bg-surface-muted text-foreground">
      <img
        src="/association-background.webp"
        alt=""
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 -z-10 h-full w-full object-cover object-center opacity-[0.08] grayscale blur-[3px]"
      />
      <Header
        title="MARVEL"
        items={publicNavigationItems}
        isAuthenticated={isAuthenticated}
        onLogout={handleLogout}
        logoutPending={logoutPending}
      />
      <div className="mx-auto grid w-full flex-1 max-w-[1440px] md:grid-cols-[minmax(0,1fr)_360px] lg:grid-cols-[minmax(0,1fr)_440px]">
        {/* Contenu marketing */}
        <section className="relative hidden overflow-hidden px-5 py-10 md:flex md:flex-col md:justify-center md:px-6 lg:px-10 xl:px-16">
          <div
            aria-hidden="true"
            className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_18%_65%,rgba(164,120,250,.14),transparent_30%),radial-gradient(circle_at_76%_20%,rgba(255,107,74,.09),transparent_24%)]"
          />
          <div className="relative max-w-[650px]">
            <p className="mb-5 flex items-center gap-3 text-xs font-black tracking-[0.24em] text-muted motion-safe:animate-fade-up">
              <span aria-hidden="true" className="h-px w-8 bg-primary/60" />
              ESPACE MARVEL
            </p>
            <p className="max-w-[620px] text-4xl font-black leading-[1.04] tracking-tight motion-safe:animate-fade-up [animation-delay:80ms] xl:text-6xl">
              Rejoignez le mouvement pour <span className="text-primary">donner.</span>
            </p>
            <div className="mt-8 max-w-[560px] border-l border-primary/40 pl-4 motion-safe:animate-fade-up [animation-delay:160ms]">
              <p className="text-sm leading-6 text-muted">
                Mouvement Associatif pour la Redistribution des Valeurs et l’Entraide Locale
              </p>
            </div>
            <p className="mt-8 max-w-[520px] text-lg leading-8 text-muted motion-safe:animate-fade-up [animation-delay:240ms]">
              Un seul compte pour participer à la vie de l’association, à votre rythme.
            </p>
            <ul className="mt-8 flex flex-wrap gap-3 motion-safe:animate-fade-up [animation-delay:320ms]">
              {highlights.map((item) => (
                <li
                  key={item.label}
                  className="inline-flex items-center gap-3 rounded-full border border-border bg-foreground/[0.04] px-4 py-3 text-sm font-bold transition duration-200 hover:border-secondary/50 hover:bg-foreground/[0.07] motion-safe:hover:-translate-y-0.5"
                >
                  <span className={`flex h-8 w-8 items-center justify-center rounded-full ${item.tone}`}>
                    {item.icon}
                  </span>
                  {item.label}
                </li>
              ))}
            </ul>
          </div>
        </section>

        {/* Formulaire */}
        <section className="relative flex items-center justify-center px-3 py-6 sm:px-8 md:border-l md:border-border md:px-3 lg:px-6 xl:px-10">
          <div className="mx-auto w-full max-w-[440px]">
            <div className="rounded-3xl border border-border bg-surface-raised/40 p-4 shadow-[0_24px_60px_rgba(0,0,0,.35)] sm:p-7 md:p-4 lg:p-7">
              <nav
                aria-label="Connexion ou inscription"
                className="relative grid grid-cols-2 rounded-xl bg-surface-raised p-1"
              >
                <span
                  aria-hidden="true"
                  className={`absolute inset-y-1 left-1 w-[calc(50%-4px)] rounded-lg bg-foreground shadow-sm ${
                    isRegister
                      ? 'translate-x-full motion-safe:animate-tab-to-register'
                      : 'motion-safe:animate-tab-to-login'
                  }`}
                />
                <button type="button" onClick={() => onModeChange?.('login')} className={tabClass(!isRegister)}>
                  Se connecter
                </button>
                <button type="button" onClick={() => onModeChange?.('register')} className={tabClass(isRegister)}>
                  Créer un compte
                </button>
              </nav>
              <div
                className={`mt-7 ${
                  isRegister ? 'motion-safe:animate-slide-in-right' : 'motion-safe:animate-slide-in-left'
                }`}
              >
                {children}
              </div>
            </div>
          </div>
        </section>
      </div>
      <Footer text={PUBLIC_FOOTER_TEXT} />
    </main>
  )
}