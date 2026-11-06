import { config } from './config.ts'

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
  const response = await fetch(`${config.apiUrl}${API_PREFIX}${path}`, {
    ...init,
    headers: { Accept: 'application/json', ...init.headers },
  })

  if (!response.ok) {
    throw new ApiError(response.status, `Erreur API (${response.status})`)
  }
  return (await response.json()) as T
}

export function apiGet<T>(path: string): Promise<T> {
  return apiRequest<T>(path)
}
