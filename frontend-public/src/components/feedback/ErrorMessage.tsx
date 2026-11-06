import Button from '../ui/Button.tsx'

type ErrorMessageProps = {
  message: string
  retryLabel?: string
  onRetry?: () => void
}

export default function ErrorMessage({
  message,
  retryLabel,
  onRetry,
}: ErrorMessageProps) {
  return (
    <div
      role="alert"
      className="rounded-md border border-danger/30 bg-danger/5 p-4 text-danger"
    >
      <p>{message}</p>
      {onRetry && retryLabel && (
        <Button variant="secondary" className="mt-3" onClick={onRetry}>
          {retryLabel}
        </Button>
      )}
    </div>
  )
}
