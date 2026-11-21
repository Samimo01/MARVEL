import { apiRequest } from '@/lib/api-client.ts'
import type {
  AuthResponse,
  AuthSession,
  LoginPayload,
  RegistrationPayload,
  RegistrationResponse,
} from '@/features/auth/types.ts'

export function register(payload: RegistrationPayload): Promise<RegistrationResponse> {
  const formData = new FormData()
  formData.append('firstname', payload.firstname)
  formData.append('lastname', payload.lastname)
  formData.append('email', payload.email.trim().toLowerCase())
  formData.append('password', payload.password)
  formData.append('tel', payload.tel.trim())
  if (payload.image) {
    formData.append('image', payload.image)
  }

  return apiRequest<RegistrationResponse>('/auth/register', {
    method: 'POST',
    body: formData,
  })
}

export function login(payload: LoginPayload): Promise<AuthResponse> {
  return apiRequest<AuthResponse>('/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email: payload.email.trim().toLowerCase(),
      password: payload.password,
      remember_me: payload.rememberMe ?? false,
    }),
  })
}

export function getCurrentSession(): Promise<AuthSession> {
  return apiRequest<AuthSession>('/auth/me')
}

export function logout(): Promise<{ message: string }> {
  return apiRequest<{ message: string }>('/auth/logout', {
    method: 'POST',
  })
}
