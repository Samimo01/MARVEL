import type { SVGProps } from 'react'

type IconProps = SVGProps<SVGSVGElement>

function IconSvg({ children, strokeWidth = 2, ...props }: IconProps) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      {...props}
    >
      {children}
    </svg>
  )
}

export function ArrowRightIcon(props: IconProps) {
  return (
    <IconSvg {...props}>
      <path d="M5 12h14m-7-7 7 7-7 7" />
    </IconSvg>
  )
}

export function EyeIcon(props: IconProps) {
  return (
    <IconSvg strokeWidth={1.8} {...props}>
      <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z" />
      <circle cx="12" cy="12" r="3" />
    </IconSvg>
  )
}

export function EyeOffIcon(props: IconProps) {
  return (
    <IconSvg strokeWidth={1.8} {...props}>
      <path d="M3 3l18 18" />
      <path d="M6.6 6.6A16.5 16.5 0 0 0 2 12s3.5 7 10 7c1.6 0 3-.4 4.3-1" />
      <path d="M9.9 5.2A9 9 0 0 1 12 5c6.5 0 10 7 10 7a17 17 0 0 1-2.6 3.4" />
    </IconSvg>
  )
}

export function HandHeartIcon(props: IconProps) {
  return (
    <IconSvg strokeWidth={1.8} {...props}>
      <path d="M12 12.5S7.5 9.7 7.5 7.1a2.5 2.5 0 0 1 4.5-1.5 2.5 2.5 0 0 1 4.5 1.5c0 2.6-4.5 5.4-4.5 5.4Z" />
      <path d="M3 15.5h3l2 2.2c.5.5 1.1.8 1.8.8h4.5c.7 0 1.3-.3 1.7-.8l4-4.2a1.2 1.2 0 0 0-1.7-1.7l-2.5 2.1h-3.3" />
      <path d="M3 15.5v5h5" />
    </IconSvg>
  )
}

export function HeartIcon(props: IconProps) {
  return (
    <IconSvg {...props}>
      <path d="M12 20s-7-4.35-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.65-7 10-7 10z" />
    </IconSvg>
  )
}

export function LockIcon(props: IconProps) {
  return (
    <IconSvg {...props}>
      <rect x="5" y="11" width="14" height="9" rx="2" />
      <path d="M8 11V8a4 4 0 0 1 8 0v3" />
    </IconSvg>
  )
}

export function LogoutIcon(props: IconProps) {
  return (
    <IconSvg {...props}>
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
      <path d="m16 17 5-5-5-5M21 12H9" />
    </IconSvg>
  )
}

export function MoonIcon(props: IconProps) {
  return (
    <IconSvg strokeWidth={1.8} {...props}>
      <path d="M20.2 15.1A8.5 8.5 0 0 1 8.9 3.8 8.5 8.5 0 1 0 20.2 15.1Z" />
    </IconSvg>
  )
}

export function SunIcon(props: IconProps) {
  return (
    <IconSvg strokeWidth={1.8} {...props}>
      <circle cx="12" cy="12" r="3.5" />
      <path d="M12 2v2m0 16v2M4.93 4.93l1.42 1.42m11.3 11.3 1.42 1.42M2 12h2m16 0h2M4.93 19.07l1.42-1.42m11.3-11.3 1.42-1.42" />
    </IconSvg>
  )
}

export function UserIcon(props: IconProps) {
  return (
    <IconSvg {...props}>
      <circle cx="12" cy="8" r="4" />
      <path d="M4 21v-2a8 8 0 0 1 16 0v2" />
    </IconSvg>
  )
}

export function UsersIcon(props: IconProps) {
  return (
    <IconSvg {...props}>
      <circle cx="9" cy="8" r="3" />
      <path d="M3 20v-1a5 5 0 0 1 5-5h2a5 5 0 0 1 5 5v1" />
      <circle cx="17" cy="9" r="2.5" />
      <path d="M17 14a4 4 0 0 1 4 4v2" />
    </IconSvg>
  )
}

type MenuIconProps = {
  open: boolean
}

export function MenuIcon({ open }: MenuIconProps) {
  return (
    <span aria-hidden="true" className="relative block h-3.5 w-5">
      <span className={`absolute left-0 top-0 h-0.5 w-full rounded bg-current transition-all duration-300 ${open ? 'translate-y-[6px] rotate-45' : ''}`} />
      <span className={`absolute left-0 top-[6px] h-0.5 w-full rounded bg-current transition-all duration-300 ${open ? 'opacity-0' : ''}`} />
      <span className={`absolute left-0 top-[12px] h-0.5 w-full rounded bg-current transition-all duration-300 ${open ? '-translate-y-[6px] -rotate-45' : ''}`} />
    </span>
  )
}
