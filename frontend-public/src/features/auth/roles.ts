import type { RoleName } from '@/features/auth/types.ts'

const backofficeRoles: ReadonlySet<RoleName> = new Set([
  'Collection_Manager',
  'Stock_Manager',
  'Treasurer',
  'Administrator',
])

export function hasBackofficeAccess(roles: readonly RoleName[]): boolean {
  return roles.some((role) => backofficeRoles.has(role))
}
