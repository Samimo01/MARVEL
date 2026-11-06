type SpinnerProps = { label: string }

export default function Spinner({ label }: SpinnerProps) {
  return (
    <p role="status" className="text-muted">
      {label}
    </p>
  )
}
