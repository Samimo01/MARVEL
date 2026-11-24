import { useEffect, useState, type FormEvent } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'

import ErrorMessage from '@/components/feedback/ErrorMessage.tsx'
import Button from '@/components/ui/Button.tsx'
import PasswordInput from '@/components/ui/PasswordInput.tsx'
import TextInput from '@/components/ui/TextInput.tsx'
import AuthLayout from '@/features/auth/components/AuthLayout.tsx'
import AuthFormHeading from '@/features/auth/components/AuthFormHeading.tsx'
import PasswordStrength from '@/features/auth/components/PasswordStrength.tsx'
import { login, register } from '@/features/auth/api.ts'
import { hasBackofficeAccess } from '@/features/auth/roles.ts'
import { useAuth } from '@/features/auth/useAuth.ts'
import { ApiError } from '@/lib/api-client.ts'
import { config } from '@/lib/config.ts'

type AuthMode = 'login' | 'register'

export default function AuthPage() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const mode: AuthMode = searchParams.get('mode') === 'register' ? 'register' : 'login'
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

  function changeMode(nextMode: AuthMode) {
    setError('')
    setPending(false)
    setSearchParams({ mode: nextMode }, { replace: true })
  }

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    const data = new FormData(event.currentTarget)
    const email = String(data.get('email') ?? '').trim()
    const passwordValue = String(data.get('password') ?? '')
    const rememberMe = data.get('rememberMe') === 'on'
    if (!email || !passwordValue) {
      setError('Veuillez renseigner votre adresse email et votre mot de passe.')
      return
    }

    setPending(true)
    try {
      await login({ email, password: passwordValue, rememberMe })
      const session = await refreshSession()
      if (!session) throw new Error('La session n’a pas pu être vérifiée après la connexion.')
      if (hasBackofficeAccess(session.roles)) {
        window.location.assign(config.adminUrl)
        return
      }
      navigate('/')
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : 'Impossible de se connecter.')
    } finally {
      setPending(false)
    }
  }

  async function handleRegister(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')

    const data = new FormData(event.currentTarget)
    const firstname = String(data.get('firstname') ?? '').trim()
    const lastname = String(data.get('lastname') ?? '').trim()
    const email = String(data.get('email') ?? '').trim()
    const tel = String(data.get('tel') ?? '').trim()

    if (firstname.length < 2 || firstname.length > 100) {
      setError('Le prénom doit contenir entre 2 et 100 caractères.')
      return
    }
    if (lastname.length < 2 || lastname.length > 100) {
      setError('Le nom doit contenir entre 2 et 100 caractères.')
      return
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setError('Veuillez saisir une adresse email valide.')
      return
    }
    if (password.length < 8 || password.length > 128) {
      setError('Le mot de passe doit contenir entre 8 et 128 caractères.')
      return
    }
    if (password !== confirmPassword) {
      setError('Les deux mots de passe ne correspondent pas.')
      return
    }
    if (!/^0[567]\d{8}$/.test(tel)) {
      setError('Le téléphone doit commencer par 05, 06 ou 07 et contenir 10 chiffres.')
      return
    }
    if (!acceptedTerms) {
      setError("Veuillez accepter les conditions d'utilisation et la politique de confidentialité.")
      return
    }
    if (image && !image.type.startsWith('image/')) {
      setError("Le fichier fourni n'est pas une image.")
      return
    }

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

  const isRegister = mode === 'register'
  const confirmInvalid = confirmTouched && confirmPassword !== password

  return (
    <AuthLayout mode={mode} onModeChange={changeMode}>
      {isRegister ? (
        <RegisterForm
          error={error}
          pending={pending}
          password={password}
          confirmPassword={confirmPassword}
          confirmInvalid={confirmInvalid}
          previewUrl={previewUrl}
          acceptedTerms={acceptedTerms}
          onPasswordChange={setPassword}
          onConfirmPasswordChange={setConfirmPassword}
          onConfirmBlur={() => setConfirmTouched(true)}
          onAcceptedTermsChange={setAcceptedTerms}
          onImageChange={(selected) => {
            setImage(selected)
            if (previewUrl) URL.revokeObjectURL(previewUrl)
            setPreviewUrl(selected ? URL.createObjectURL(selected) : '')
          }}
          onSubmit={handleRegister}
        />
      ) : (
        <LoginForm error={error} pending={pending} onSubmit={handleLogin} />
      )}
    </AuthLayout>
  )
}

type LoginFormProps = {
  error: string
  pending: boolean
  onSubmit: (event: FormEvent<HTMLFormElement>) => void
}

function LoginForm({ error, pending, onSubmit }: LoginFormProps) {
  return (
    <>
      <AuthFormHeading
        title="Heureux de vous revoir"
        description="Connectez-vous à votre espace."
      />
      {error && (
        <div className="mb-4 motion-safe:animate-fade-up">
          <ErrorMessage message={error} />
        </div>
      )}
      <form className="mt-4 space-y-4" onSubmit={onSubmit}>
        <TextInput name="email" type="email" placeholder="Adresse e-mail" aria-label="Adresse e-mail" autoComplete="email" required />
        <PasswordInput name="password" placeholder="Mot de passe" aria-label="Mot de passe" autoComplete="current-password" required />
        <label className="flex cursor-pointer items-center gap-3 text-sm text-muted">
          <input
            className="h-4 w-4 cursor-pointer accent-primary"
            name="rememberMe"
            type="checkbox"
          />
          Rester connecté
        </label>
        <Button type="submit" loading={pending}>
          {pending ? 'Connexion...' : <>Se connecter <span aria-hidden="true" className="transition-transform duration-200 group-hover:translate-x-1">→</span></>}
        </Button>
      </form>
    </>
  )
}

type RegisterFormProps = {
  error: string
  pending: boolean
  password: string
  confirmPassword: string
  confirmInvalid: boolean
  previewUrl: string
  acceptedTerms: boolean
  onPasswordChange: (value: string) => void
  onConfirmPasswordChange: (value: string) => void
  onConfirmBlur: () => void
  onAcceptedTermsChange: (value: boolean) => void
  onImageChange: (image: File | undefined) => void
  onSubmit: (event: FormEvent<HTMLFormElement>) => void
}

function RegisterForm({
  error,
  pending,
  password,
  confirmPassword,
  confirmInvalid,
  previewUrl,
  acceptedTerms,
  onPasswordChange,
  onConfirmPasswordChange,
  onConfirmBlur,
  onAcceptedTermsChange,
  onImageChange,
  onSubmit,
}: RegisterFormProps) {
  return (
    <>
      <AuthFormHeading title="Créez votre compte" description="Gratuit, en moins d’une minute." />
      {error && (
        <div className="mb-4 motion-safe:animate-fade-up">
          <ErrorMessage message={error} />
        </div>
      )}
      <form className="mt-4 space-y-3" onSubmit={onSubmit}>
        <div className="grid gap-3 sm:grid-cols-2">
          <TextInput name="firstname" placeholder="Prénom" aria-label="Prénom" autoComplete="given-name" required />
          <TextInput name="lastname" placeholder="Nom" aria-label="Nom" autoComplete="family-name" required />
        </div>
        <TextInput name="email" type="email" placeholder="Adresse e-mail" aria-label="Adresse e-mail" autoComplete="email" required />
        <PasswordInput
          name="password"
          value={password}
          onChange={(event) => onPasswordChange(event.target.value)}
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
          onChange={(event) => onConfirmPasswordChange(event.target.value)}
          onBlur={onConfirmBlur}
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
        <TextInput name="tel" type="tel" inputMode="tel" minLength={10} maxLength={10} placeholder="Téléphone — 0612345678" aria-label="Téléphone" autoComplete="tel" required />
        <label className="block text-xs text-muted">
          <span className="mb-2 block">Photo de profil (facultative)</span>
          <input
            className="block w-full cursor-pointer text-xs file:mr-3 file:min-h-10 file:cursor-pointer file:rounded-lg file:border-0 file:bg-surface-raised file:px-3 file:text-foreground file:transition-colors file:duration-200 hover:file:bg-secondary/30"
            name="image"
            type="file"
            accept="image/*"
            onChange={(event) => onImageChange(event.target.files?.[0])}
          />
        </label>
        {previewUrl && <img className="h-16 w-16 rounded-full border border-border object-cover" src={previewUrl} alt="Prévisualisation de la photo de profil" />}
        <label className="flex cursor-pointer gap-3 text-xs leading-5 text-muted">
          <input type="checkbox" className="mt-1 h-4 w-4 shrink-0 cursor-pointer accent-primary" checked={acceptedTerms} onChange={(event) => onAcceptedTermsChange(event.target.checked)} />
          <span className="min-w-0">
            J’accepte les <a href="/conditions" target="_blank" rel="noopener" className="text-foreground underline decoration-primary underline-offset-2">conditions d’utilisation</a> et la{' '}
            <a href="/confidentialite" target="_blank" rel="noopener" className="text-foreground underline decoration-primary underline-offset-2">politique de confidentialité</a>.
          </span>
        </label>
        <Button type="submit" loading={pending} className="mt-2">
          {pending ? 'Création...' : <>Créer mon compte <span aria-hidden="true" className="transition-transform duration-200 group-hover:translate-x-1">→</span></>}
        </Button>
      </form>
    </>
  )
}
