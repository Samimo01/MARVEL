import { config } from '@/app/config'

let refreshRequest: Promise<boolean> | null = null

function refreshAccessToken(): Promise<boolean> {
  if (!refreshRequest) {
    const apiUrl = config.apiUrl.replace(/\/+$/, '')
    const request = fetch(`${apiUrl}/api/v1/auth/refresh`, {
      method: 'POST',
      credentials: 'include',
      headers: { Accept: 'application/json' },
    })
      .then((response) => response.ok)
      .finally(() => {
        refreshRequest = null
      })
    refreshRequest = request
  }
  return refreshRequest
}

export async function fetchWithSessionRefresh(
  url: string,
  init: RequestInit = {},
): Promise<Response> {
  const response = await fetch(url, init)
  const pathname = new URL(url, window.location.href).pathname
  if (
    response.status !== 401 ||
    ['/auth/login', '/auth/register', '/auth/refresh'].some((path) =>
      pathname.endsWith(path),
    ) ||
    !(await refreshAccessToken())
  ) {
    return response
  }

  return fetch(url, init)
}
