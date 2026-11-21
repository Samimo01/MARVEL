import { useCallback, useEffect, useState, type ReactNode } from 'react'

import { getCurrentSession, logout as logoutRequest } from '@/features/auth/api.ts'
import { AuthContext } from '@/features/auth/auth-context.ts'
import { hasBackofficeAccess } from '@/features/auth/roles.ts'
import type { AuthSession } from '@/features/auth/types.ts'
import { ApiError } from '@/lib/api-client.ts'
import { config } from '@/lib/config.ts'

function getSessionErrorMessage(error: unknown): string {
  if (error instanceof ApiError && error.status === 404) {
    return "La vérification de session est indisponible. Le backend doit être mis à jour."
  }
  return error instanceof Error
    ? error.message
    : 'Impossible de vérifier la session. Réessayez.'
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<AuthSession | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [authError, setAuthError] = useState<string | null>(null)

  const refreshSession = useCallback(async () => {
    setIsLoading(true)
    try {
      const currentSession = await getCurrentSession()
      setSession(currentSession)
      setAuthError(null)
      return currentSession
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        setSession(null)
        setAuthError(null)
        return null
      }

      setAuthError(getSessionErrorMessage(error))
      throw error
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    let active = true
    getCurrentSession()
      .then((currentSession) => {
        if (!active) return
        setSession(currentSession)
        setAuthError(null)
        if (
          currentSession &&
          hasBackofficeAccess(currentSession.roles) &&
          new URL(config.adminUrl).origin !== window.location.origin
        ) {
          window.location.replace(config.adminUrl)
        }
      })
      .catch((error) => {
        if (!active) return
        if (
          error instanceof ApiError &&
          (error.status === 401 || error.status === 404)
        ) {
          setSession(null)
          setAuthError(null)
          return
        }

        setAuthError(getSessionErrorMessage(error))
      })
      .finally(() => {
        if (active) setIsLoading(false)
      })

    return () => {
      active = false
    }
  }, [])

  const logout = useCallback(async () => {
    setAuthError(null)
    try {
      await logoutRequest()
      setSession(null)
    } catch (error) {
      setAuthError(
        error instanceof Error ? error.message : 'Impossible de fermer la session.',
      )
      throw error
    }
  }, [])

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated: Boolean(session),
        isLoading,
        roles: session?.roles ?? [],
        authError,
        refreshSession,
        logout,
      }}
    >
      {children}
      {authError && (
        <p
          role="alert"
          className="fixed bottom-4 left-4 z-[100] rounded-xl border border-danger/40 bg-surface-raised px-4 py-3 text-sm text-danger shadow-lg"
        >
          {authError}
        </p>
      )}
    </AuthContext.Provider>
  )
}
