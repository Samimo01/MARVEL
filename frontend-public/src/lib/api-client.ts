import { config } from '@/lib/config.ts'

/** Préfixe commun de toutes les routes de l'API (versionnée). */
export const API_PREFIX = '/api/v1'

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

/**
 * Client API centralisé : c'est le SEUL endroit où l'on appelle `fetch`.
 * Les features l'utilisent via leur fichier `api.ts`.
 */
export async function apiRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers)
  headers.set('Accept', 'application/json')

  const response = await fetch(`${config.apiUrl}${API_PREFIX}${path}`, {
    ...init,
    headers,
    credentials: 'include',
  })

  if (!response.ok) {
    let message = `Erreur API (${response.status})`
    try {
      const body = (await response.json()) as
        | { detail?: string | Array<{ msg?: string }> }
        | undefined
      if (typeof body?.detail === 'string') {
        message = body.detail
      } else if (Array.isArray(body?.detail)) {
        message =
          body.detail
            .map((item) => item.msg)
            .filter((item): item is string => Boolean(item))
            .join(' ') || message
      }
    } catch {
      // Conserve le message HTTP générique si la réponse n'est pas du JSON.
    }
    throw new ApiError(response.status, message)
  }
  return (await response.json()) as T
}

export function apiGet<T>(path: string): Promise<T> {
  return apiRequest<T>(path)
}
