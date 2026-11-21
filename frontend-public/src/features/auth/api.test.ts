import { getCurrentSession, login, register } from '@/features/auth/api.ts'

afterEach(() => {
  vi.unstubAllGlobals()
  localStorage.clear()
  sessionStorage.clear()
})

describe('auth api', () => {
  it('normalise l’inscription et envoie les champs en multipart', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        message: 'Compte créé.',
        id_user: 'user-id',
        nickname: null,
        image_url: null,
      }),
    })
    vi.stubGlobal('fetch', fetchMock)

    await register({
      firstname: 'Ada',
      lastname: 'Lovelace',
      email: ' Ada@Example.com ',
      password: 'a-very-strong-password',
      tel: '0612345678',
    })

    const init = fetchMock.mock.calls[0][1] as RequestInit
    const body = init.body as FormData
    expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/auth/register')
    expect(init.method).toBe('POST')
    expect(init.credentials).toBe('include')
    expect(body.get('email')).toBe('ada@example.com')
    expect(body.get('tel')).toBe('0612345678')
  })

  it('normalise la connexion et envoie un corps JSON', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ message: 'Connexion réussie.' }),
    })
    vi.stubGlobal('fetch', fetchMock)

    await login({
      email: ' ADA@Example.com ',
      password: 'a-very-strong-password',
    })

    const init = fetchMock.mock.calls[0][1] as RequestInit
    expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/auth/login')
    expect(JSON.parse(String(init.body))).toEqual({
      email: 'ada@example.com',
      password: 'a-very-strong-password',
      remember_me: false,
    })
    expect(init.credentials).toBe('include')
  })

  it('récupère les rôles de la session via le cookie HttpOnly', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        id_user: 'user-id',
        roles: ['Collection_Manager'],
      }),
    })
    vi.stubGlobal('fetch', fetchMock)

    await expect(getCurrentSession()).resolves.toEqual({
      id_user: 'user-id',
      roles: ['Collection_Manager'],
    })
    expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/auth/me')
    expect((fetchMock.mock.calls[0][1] as RequestInit).credentials).toBe('include')
  })
})
