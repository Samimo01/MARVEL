import { NavLink } from 'react-router-dom'

import { UserIcon } from '@/components/icons/index.tsx'
import { focusRing } from '@/components/layout/classes.ts'

type JoinButtonProps = {
  compact?: boolean
  onClick?: () => void
}

export default function JoinButton({ compact = false, onClick }: JoinButtonProps) {
  const className = compact
    ? `inline-flex min-h-12 items-center justify-center rounded-2xl bg-gradient-to-b from-primary to-primary-hover px-5 font-bold text-primary-foreground shadow-[0_6px_18px_rgba(255,107,74,.28)] ring-1 ring-inset ring-white/20 transition duration-300 motion-reduce:transition-none ${focusRing}`
    : `inline-flex h-10 items-center gap-2 rounded-full bg-gradient-to-b from-primary to-primary-hover px-5 text-sm font-bold text-primary-foreground shadow-[0_6px_18px_rgba(255,107,74,.28)] ring-1 ring-inset ring-white/20 transition duration-200 hover:shadow-[0_10px_26px_rgba(255,107,74,.4)] motion-safe:hover:-translate-y-0.5 active:translate-y-0 ${focusRing}`

  return (
    <NavLink to="/auth?mode=register" onClick={onClick} className={className}>
      {!compact && <UserIcon className="h-4 w-4" />}
      Nous rejoindre
    </NavLink>
  )
}
