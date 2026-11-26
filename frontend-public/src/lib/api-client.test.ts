import { ApiError, apiGet } from '@/lib/api-client.ts'

afterEach(() => vi.unstubAllGlobals())

describe('api-client', () => {
  it('appelle le préfixe /api/v1 et renvoie le JSON', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue({ ok: true, json: async () => [{ id: 1 }] })
    vi.stubGlobal('fetch', fetchMock)

    await expect(apiGet('/public/campaigns')).resolves.toEqual([{ id: 1 }])
    expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/public/campaigns')
  })

  it('lève une ApiError quand la réponse est en erreur', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 500 }))
    await expect(apiGet('/x')).rejects.toBeInstanceOf(ApiError)
  })

  it('renouvelle la session puis réessaie une requête protégée après un 401', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({ ok: false, status: 401 })
      .mockResolvedValueOnce({ ok: true, status: 200 })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ id: 1 }) })
    vi.stubGlobal('fetch', fetchMock)

    await expect(apiGet('/users/me')).resolves.toEqual({ id: 1 })

    expect(fetchMock).toHaveBeenCalledTimes(3)
    expect(fetchMock.mock.calls[1][0]).toBe('/api/v1/auth/refresh')
    expect(fetchMock.mock.calls[1][1]).toMatchObject({
      method: 'POST',
      credentials: 'include',
    })
    expect(fetchMock.mock.calls[2][0]).toBe('/api/v1/users/me')
  })

  it('ne tente pas de renouveler une connexion refusée', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue({ ok: false, status: 401, json: async () => ({}) })
    vi.stubGlobal('fetch', fetchMock)

    await expect(apiGet('/auth/login')).rejects.toBeInstanceOf(ApiError)
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })
})
