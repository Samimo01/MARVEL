import { useEffect, useState, type ReactNode } from 'react'

import { config } from '@/app/config'
import { fetchWithSessionRefresh } from '@/app/api-client'

const backofficeRoles = new Set([
  'Collection_Manager',
  'Stock_Manager',
  'Treasurer',
  'Administrator',
])

type SessionResponse = {
  roles: string[]
}

type BackofficeGuardProps = {
  children: ReactNode
}

export default function BackofficeGuard({ children }: BackofficeGuardProps) {
  const [authorized, setAuthorized] = useState(false)
  const [error, setError] = useState('')
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    const controller = new AbortController()

    async function verifyAccess() {
      setError('')
      setAuthorized(false)

      try {
        const apiUrl = config.apiUrl.replace(/\/+$/, '')
        const response = await fetchWithSessionRefresh(`${apiUrl}/api/v1/users/me`, {
          credentials: 'include',
          headers: { Accept: 'application/json' },
          signal: controller.signal,
        })

        if (response.status === 401) {
          window.location.replace(`${config.publicUrl.replace(/\/+$/, '')}/auth?mode=login`)
          return
        }
        if (!response.ok) {
          throw new Error(`Impossible de vérifier les accès (${response.status}).`)
        }

        const session = (await response.json()) as SessionResponse
        if (!session.roles.some((role) => backofficeRoles.has(role))) {
          window.location.replace(config.publicUrl)
          return
        }
        setAuthorized(true)
      } catch (caught) {
        if (caught instanceof Error && caught.name === 'AbortError') return
        setError(
          caught instanceof Error
            ? caught.message
            : 'Impossible de vérifier les accès au backoffice.',
        )
      }
    }

    void verifyAccess()
    return () => controller.abort()
  }, [attempt])

  if (error) {
    return (
      <main className="flex min-h-screen items-center justify-center p-6">
        <div className="max-w-md space-y-4 text-center">
          <p role="alert">{error}</p>
          <button
            type="button"
            className="rounded-lg bg-primary px-4 py-2 text-primary-foreground"
            onClick={() => setAttempt((value) => value + 1)}
          >
            Réessayer
          </button>
        </div>
      </main>
    )
  }

  if (!authorized) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p role="status">Vérification des accès au backoffice…</p>
      </main>
    )
  }

  return children
}
