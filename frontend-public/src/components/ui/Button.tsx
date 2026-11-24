import type { ButtonHTMLAttributes } from 'react'

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  loading?: boolean
  variant?: 'primary' | 'secondary'
}

/** Bouton principal : hover, appui, désactivé et chargement. Le libellé est fourni par l'appelant. */
export default function Button({
  loading = false,
  disabled,
  className = '',
  children,
  variant = 'primary',
  ...props
}: ButtonProps) {
  const variantClasses =
    variant === 'secondary'
      ? 'border border-border bg-surface-raised text-foreground shadow-none hover:bg-foreground/5 hover:shadow-none'
      : 'bg-primary text-primary-foreground shadow-[0_12px_30px_rgba(255,107,74,.22)] hover:bg-primary-hover hover:shadow-[0_16px_36px_rgba(255,107,74,.32)]'

  return (
    <button
      {...props}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      className={`group inline-flex min-h-14 w-full items-center justify-center gap-2 rounded-xl px-5 font-black transition duration-200 motion-safe:hover:-translate-y-0.5 active:translate-y-0 active:scale-[.99] disabled:cursor-not-allowed disabled:opacity-60 disabled:shadow-none disabled:hover:translate-y-0 ${variantClasses} ${className}`}
    >
      {loading && (
        <span
          aria-hidden="true"
          className="h-4 w-4 rounded-full border-2 border-current border-t-transparent motion-safe:animate-spin"
        />
      )}
      {children}
    </button>
  )
}