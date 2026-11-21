import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { useAuth } from '@/features/auth/useAuth.ts'

export default function useHeaderAuthActions() {
  const { isAuthenticated, logout } = useAuth()
  const navigate = useNavigate()
  const [logoutPending, setLogoutPending] = useState(false)

  async function handleLogout() {
    setLogoutPending(true)
    try {
      await logout()
      navigate('/auth?mode=login')
    } finally {
      setLogoutPending(false)
    }
  }

  return { isAuthenticated, logoutPending, handleLogout }
}
