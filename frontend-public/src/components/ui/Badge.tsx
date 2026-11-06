import type { HTMLAttributes } from 'react'

type BadgeProps = HTMLAttributes<HTMLSpanElement> & {
  tone?: 'neutral' | 'success' | 'warning' | 'danger'
}

const tones = {
  neutral: 'bg-surface-muted text-muted',
  success: 'bg-success/10 text-success',
  warning: 'bg-warning/10 text-warning',
  danger: 'bg-danger/10 text-danger',
}

export default function Badge({
  tone = 'neutral',
  className = '',
  ...props
}: BadgeProps) {
  return (
    <span
      className={`inline-block rounded-full px-2 py-0.5 text-sm font-medium ${tones[tone]} ${className}`}
      {...props}
    />
  )
}
