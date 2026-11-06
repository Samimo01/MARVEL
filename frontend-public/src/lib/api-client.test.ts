import { ApiError, apiGet } from './api-client.ts'

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
})
