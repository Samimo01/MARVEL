type ProgressBarProps = {
  value: number
  max: number
  /** Libellé accessible de la jauge (fourni par l'appelant). */
  label: string
}

/** Jauge générique : n'affiche que ce qu'on lui donne. */
export default function ProgressBar({ value, max, label }: ProgressBarProps) {
  const percent = max > 0 ? Math.min(100, Math.max(0, (value / max) * 100)) : 0

  return (
    <div
      role="progressbar"
      aria-label={label}
      aria-valuemin={0}
      aria-valuemax={max}
      aria-valuenow={value}
      className="h-3 w-full overflow-hidden rounded-full bg-surface-muted"
    >
      {/* Largeur réellement dynamique : seul cas autorisé de style en ligne */}
      <div className="h-full bg-primary" style={{ width: `${percent}%` }} />
    </div>
  )
}
