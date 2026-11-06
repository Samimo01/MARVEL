import type { HTMLAttributes } from 'react'

export default function Card({
  className = '',
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={`rounded-md border border-border bg-surface p-4 shadow-sm ${className}`}
      {...props}
    />
  )
}
