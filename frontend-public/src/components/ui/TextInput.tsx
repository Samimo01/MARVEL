import type { InputHTMLAttributes } from 'react'

type TextInputProps = InputHTMLAttributes<HTMLInputElement> & {
  invalid?: boolean
}

/** Champ de saisie générique : survol, focus clavier, état invalide et désactivé. */
export default function TextInput({ invalid = false, className = '', ...props }: TextInputProps) {
  return (
    <input
      aria-invalid={invalid || undefined}
      className={`min-h-14 w-full rounded-xl border bg-surface-raised px-4 text-sm text-foreground outline-none transition duration-200 placeholder:text-muted/60 focus-visible:ring-4 disabled:cursor-not-allowed disabled:opacity-60 ${
        invalid
          ? 'border-danger/70 focus-visible:border-danger focus-visible:ring-danger/20'
          : 'border-border hover:border-secondary/50 focus-visible:border-secondary focus-visible:ring-secondary/20'
      } ${className}`}
      {...props}
    />
  )
}