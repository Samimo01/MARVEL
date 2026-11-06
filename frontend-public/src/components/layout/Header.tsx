import { NavLink } from 'react-router-dom'

export type NavItem = { to: string; label: string }

type HeaderProps = { title: string; items: NavItem[] }

export default function Header({ title, items }: HeaderProps) {
  return (
    <header className="border-b border-border bg-surface">
      <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-2 px-4 py-3">
        <span className="text-lg font-semibold text-primary">{title}</span>
        <nav aria-label="Navigation principale" className="flex gap-4">
          {items.map((item) => (
            <NavLink key={item.to} to={item.to} end className="font-medium">
              {item.label}
            </NavLink>
          ))}
        </nav>
      </div>
    </header>
  )
}
