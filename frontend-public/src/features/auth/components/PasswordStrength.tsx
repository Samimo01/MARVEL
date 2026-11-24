type PasswordStrengthProps = {
  password: string
}

const rules = [
  { label: '8 caractères', test: (value: string) => value.length >= 8 },
  { label: 'Maj. + min.', test: (value: string) => /[a-z]/.test(value) && /[A-Z]/.test(value) },
  { label: 'Chiffre ou symbole', test: (value: string) => /[\d\W_]/.test(value) },
]

const verdicts = ['', 'Faible', 'Moyen', 'Bon', 'Excellent']

/**
 * Indicateur purement informatif : la validation réelle (8 à 128 caractères)
 * reste celle du formulaire et du backend.
 */
export default function PasswordStrength({ password }: PasswordStrengthProps) {
  const results = rules.map((rule) => ({ label: rule.label, met: rule.test(password) }))
  const score = password
    ? results.filter((result) => result.met).length + (password.length >= 12 ? 1 : 0)
    : 0
  const tone = score <= 1 ? 'bg-danger' : score === 2 ? 'bg-warning' : 'bg-success'

  return (
    <div className="px-1">
      <div className="flex gap-1.5" aria-hidden="true">
        {[0, 1, 2, 3].map((index) => (
          <span
            key={index}
            className={`h-1 flex-1 rounded-full transition-colors duration-300 ${
              index < score ? tone : 'bg-foreground/10'
            }`}
          />
        ))}
      </div>
      <p className="sr-only" aria-live="polite">
        {verdicts[score] ? `Force du mot de passe : ${verdicts[score]}` : ''}
      </p>
      <ul className="mt-2 grid grid-cols-3 gap-2 text-[11px]">
        {results.map(({ label, met }) => (
          <li
            key={label}
            className={`flex items-center gap-1.5 transition-colors duration-300 ${
              met ? 'text-success' : 'text-muted/70'
            }`}
          >
            <span
              aria-hidden="true"
              className={`h-2.5 w-2.5 shrink-0 rounded-full border transition-colors duration-300 ${
                met ? 'border-success bg-success' : 'border-current'
              }`}
            />
            <span>
              {label}
              <span className="sr-only">{met ? ' : validé' : ' : non validé'}</span>
            </span>
          </li>
        ))}
      </ul>
    </div>
  )
}