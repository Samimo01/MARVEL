import { createContext } from 'react'

import type { AuthSession, RoleName } from '@/features/auth/types.ts'

export type AuthContextValue = {
  isAuthenticated: boolean
  isLoading: boolean
  roles: RoleName[]
  authError: string | null
  refreshSession: () => Promise<AuthSession | null>
  logout: () => Promise<void>
}

export const AuthContext = createContext<AuthContextValue | null>(null)
