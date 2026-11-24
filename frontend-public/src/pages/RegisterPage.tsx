import { useEffect, useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import ErrorMessage from '@/components/feedback/ErrorMessage.tsx'
import Button from '@/components/ui/Button.tsx'
import PasswordInput from '@/components/ui/PasswordInput.tsx'
import TextInput from '@/components/ui/TextInput.tsx'
import AuthLayout from '@/features/auth/components/AuthLayout.tsx'
import AuthFormHeading from '@/features/auth/components/AuthFormHeading.tsx'
import PasswordStrength from '@/features/auth/components/PasswordStrength.tsx'
import { register } from '@/features/auth/api.ts'
import { useAuth } from '@/features/auth/useAuth.ts'
import { ApiError } from '@/lib/api-client.ts'

export default function RegisterPage() {
  const navigate = useNavigate()
  const { refreshSession } = useAuth()
  const [error, setError] = useState('')
  const [pending, setPending] = useState(false)
  const [image, setImage] = useState<File | undefined>()
  const [previewUrl, setPreviewUrl] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [confirmTouched, setConfirmTouched] = useState(false)
  const [acceptedTerms, setAcceptedTerms] = useState(false)

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl)
    }
  }, [previewUrl])

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')

    const data = new FormData(event.currentTarget)
    const firstname = String(data.get('firstname') ?? '').trim()
    const lastname = String(data.get('lastname') ?? '').trim()
    const email = String(data.get('email') ?? '').trim()
    const password = String(data.get('password') ?? '')
    const tel = String(data.get('tel') ?? '').trim()

    if (firstname.length < 2 || firstname.length > 100)
      return setError('Le prénom doit contenir entre 2 et 100 caractères.')
    if (lastname.length < 2 || lastname.length > 100)
      return setError('Le nom doit contenir entre 2 et 100 caractères.')
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email))
      return setError('Veuillez saisir une adresse email valide.')
    if (password.length < 8 || password.length > 128)
      return setError('Le mot de passe doit contenir entre 8 et 128 caractères.')
    if (password !== confirmPassword)
      return setError('Les deux mots de passe ne correspondent pas.')
    if (!/^0[567]\d{8}$/.test(tel))
      return setError('Le téléphone doit commencer par 05, 06 ou 07 et contenir 10 chiffres.')
    if (!acceptedTerms)
      return setError("Veuillez accepter les conditions d'utilisation et la politique de confidentialité.")
    if (image && !image.type.startsWith('image/'))
      return setError("Le fichier fourni n'est pas une image.")

    setPending(true)
    try {
      await register({ firstname, lastname, email, password, tel, image })
      const session = await refreshSession()
      if (!session) throw new Error('La session n’a pas pu être vérifiée après la création du compte.')
      navigate('/')
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : 'Impossible de créer le compte.')
    } finally {
      setPending(false)
    }
  }

  const confirmInvalid = confirmTouched && confirmPassword !== password

  return (
    <AuthLayout mode="register">
      <AuthFormHeading title="Créez votre compte" description="Gratuit, en moins d’une minute." />
      {error && (
        <div className="motion-safe:animate-fade-up">
          <ErrorMessage message={error} />
        </div>
      )}
      <form className="mt-4 space-y-3" onSubmit={handleSubmit}>
        <div className="grid gap-3 sm:grid-cols-2">
          <TextInput name="firstname" placeholder="Prénom" aria-label="Prénom" autoComplete="given-name" required />
          <TextInput name="lastname" placeholder="Nom" aria-label="Nom" autoComplete="family-name" required />
        </div>
        <TextInput name="email" type="email" placeholder="Adresse e-mail" aria-label="Adresse e-mail" autoComplete="email" required />
        <PasswordInput
          name="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          minLength={8}
          maxLength={128}
          placeholder="Mot de passe"
          aria-label="Mot de passe"
          autoComplete="new-password"
          required
        />
        <PasswordStrength password={password} />
        <PasswordInput
          name="confirmPassword"
          value={confirmPassword}
          onChange={(event) => setConfirmPassword(event.target.value)}
          onBlur={() => setConfirmTouched(true)}
          invalid={confirmInvalid}
          aria-describedby={confirmInvalid ? 'confirm-password-hint' : undefined}
          placeholder="Confirmer le mot de passe"
          aria-label="Confirmer le mot de passe"
          autoComplete="new-password"
          required
        />
        {confirmInvalid && (
          <p id="confirm-password-hint" className="px-1 text-xs text-danger motion-safe:animate-fade-up">
            Les deux mots de passe ne correspondent pas.
          </p>
        )}
        <TextInput
          name="tel"
          type="tel"
          inputMode="tel"
          minLength={10}
          maxLength={10}
          placeholder="Téléphone — 0612345678"
          aria-label="Téléphone"
          autoComplete="tel"
          required
        />
        <label className="block text-xs text-muted">
          <span className="mb-2 block">Photo de profil (facultative)</span>
          <input
            className="block w-full cursor-pointer text-xs file:mr-3 file:min-h-10 file:cursor-pointer file:rounded-lg file:border-0 file:bg-surface-raised file:px-3 file:text-foreground file:transition-colors file:duration-200 hover:file:bg-secondary/30 focus-visible:rounded-lg"
            name="image"
            type="file"
            accept="image/*"
            onChange={(event) => {
              const selected = event.target.files?.[0]
              setImage(selected)
              if (previewUrl) URL.revokeObjectURL(previewUrl)
              setPreviewUrl(selected ? URL.createObjectURL(selected) : '')
            }}
          />
        </label>
        {previewUrl && (
          <img
            className="h-16 w-16 rounded-full border border-border object-cover motion-safe:animate-fade-up"
            src={previewUrl}
            alt="Prévisualisation de la photo de profil"
          />
        )}
        <label className="flex cursor-pointer gap-3 text-xs leading-5 text-muted">
          <input
            type="checkbox"
            className="mt-1 h-4 w-4 shrink-0 cursor-pointer accent-primary"
            checked={acceptedTerms}
            onChange={(event) => setAcceptedTerms(event.target.checked)}
          />
          <span>
            J’accepte les{' '}
            <a href="/conditions" target="_blank" rel="noopener" className="rounded-sm text-foreground underline decoration-primary underline-offset-2 transition-colors duration-200 hover:text-primary">
              conditions d’utilisation
            </a>{' '}
            et la{' '}
            <a href="/confidentialite" target="_blank" rel="noopener" className="rounded-sm text-foreground underline decoration-primary underline-offset-2 transition-colors duration-200 hover:text-primary">
              politique de confidentialité
            </a>
            .
          </span>
        </label>
        <Button type="submit" loading={pending} className="mt-2">
          {pending ? (
            'Création...'
          ) : (
            <>
              Créer mon compte
              <span aria-hidden="true" className="transition-transform duration-200 group-hover:translate-x-1">→</span>
            </>
          )}
        </Button>
      </form>
      <p className="mt-6 text-center text-sm text-muted">
        Déjà inscrit·e ?{' '}
        <Link
          to="/connexion"
          className="rounded-sm font-bold text-foreground underline decoration-primary decoration-2 underline-offset-4 transition-colors duration-200 hover:text-primary"
        >
          Se connecter
        </Link>
      </p>
    </AuthLayout>
  )
}