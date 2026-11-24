import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import ErrorMessage from '@/components/feedback/ErrorMessage.tsx'
import Button from '@/components/ui/Button.tsx'
import PasswordInput from '@/components/ui/PasswordInput.tsx'
import TextInput from '@/components/ui/TextInput.tsx'
import AuthLayout from '@/features/auth/components/AuthLayout.tsx'
import AuthFormHeading from '@/features/auth/components/AuthFormHeading.tsx'
import { login } from '@/features/auth/api.ts'
import { hasBackofficeAccess } from '@/features/auth/roles.ts'
import { useAuth } from '@/features/auth/useAuth.ts'
import { ApiError } from '@/lib/api-client.ts'
import { config } from '@/lib/config.ts'

export default function LoginPage() {
  const navigate = useNavigate()
  const { refreshSession } = useAuth()
  const [error, setError] = useState('')
  const [pending, setPending] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')

    const data = new FormData(event.currentTarget)
    const email = String(data.get('email') ?? '').trim()
    const password = String(data.get('password') ?? '')
    const rememberMe = data.get('rememberMe') === 'on'

    if (!email || !password)
      return setError('Veuillez renseigner votre adresse email et votre mot de passe.')

    setPending(true)
    try {
      await login({ email, password, rememberMe })
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

  return (
    <AuthLayout mode="login">
      <AuthFormHeading
        title="Heureux de vous revoir"
        description="Connectez-vous à votre espace."
      />
      {error && (
        <div className="motion-safe:animate-fade-up">
          <ErrorMessage message={error} />
        </div>
      )}
      <form className="mt-4 space-y-4" onSubmit={handleSubmit}>
        <TextInput
          name="email"
          type="email"
          placeholder="Adresse e-mail"
          aria-label="Adresse e-mail"
          autoComplete="email"
          required
        />
        <PasswordInput
          name="password"
          placeholder="Mot de passe"
          aria-label="Mot de passe"
          autoComplete="current-password"
          required
        />
        <label className="flex cursor-pointer items-center gap-3 text-sm text-muted">
          <input
            className="h-4 w-4 cursor-pointer accent-primary"
            name="rememberMe"
            type="checkbox"
          />
          Rester connecté
        </label>
        <Button type="submit" loading={pending}>
          {pending ? (
            'Connexion...'
          ) : (
            <>
              Se connecter
              <span aria-hidden="true" className="transition-transform duration-200 group-hover:translate-x-1">→</span>
            </>
          )}
        </Button>
      </form>
      <p className="mt-6 text-center text-sm text-muted">
        Pas encore de compte ?{' '}
        <Link
          to="/inscription"
          className="rounded-sm font-bold text-foreground underline decoration-primary decoration-2 underline-offset-4 transition-colors duration-200 hover:text-primary"
        >
          Créer un compte
        </Link>
      </p>
    </AuthLayout>
  )
}