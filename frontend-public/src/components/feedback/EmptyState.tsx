type EmptyStateProps = { message: string }

export default function EmptyState({ message }: EmptyStateProps) {
  return (
    <p className="rounded-md border border-dashed border-border p-6 text-center text-muted">
      {message}
    </p>
  )
}
