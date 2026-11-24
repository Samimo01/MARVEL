import { HandHeartIcon, MoonIcon, SunIcon } from '@/components/icons/index.tsx'

type HeaderUtilitiesProps = {
  showMoon: boolean
  onToggleThemeIcon: () => void
}

export default function HeaderUtilities({
  showMoon,
  onToggleThemeIcon,
}: HeaderUtilitiesProps) {
  return (
    <div className="flex items-center gap-2">
      <button
        type="button"
        className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-border/60 bg-foreground/5 text-muted transition-colors duration-200 hover:bg-foreground/10 hover:text-foreground disabled:cursor-not-allowed disabled:opacity-70 disabled:hover:bg-foreground/5 disabled:hover:text-muted"
        aria-label={`Icône ${showMoon ? 'lune' : 'soleil'} affichée (thème inchangé)`}
        aria-pressed={showMoon}
        title="Basculer l’icône soleil / lune — le thème ne change pas encore"
        onClick={onToggleThemeIcon}
      >
        {showMoon ? <MoonIcon className="h-4 w-4" /> : <SunIcon className="h-4 w-4 text-primary" />}
        <span className="sr-only">Mode clair / sombre</span>
      </button>

      <button
        type="button"
        className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-primary/40 bg-primary/10 text-primary disabled:cursor-not-allowed disabled:opacity-100"
        aria-label="Faire un don, bientôt disponible"
        title="Faire un don — bientôt disponible"
        disabled
      >
        <HandHeartIcon className="h-5 w-5" />
        <span className="sr-only">Faire un don</span>
      </button>
    </div>
  )
}