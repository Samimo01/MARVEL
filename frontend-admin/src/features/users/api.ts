import { apiRequest } from "@/app/api-client";
import type { RoleAssignment } from "@/features/users/types";
export const listRoles = () => apiRequest<string[]>("/admin/roles");
export const listUserRoleAssignments = (id: string) =>
  apiRequest<RoleAssignment[]>(`/admin/users/${id}/roles`);
export const setUserRole = (
  id: string,
  role: string,
  assignment_type: "assigned" | "revoked",
) =>
  apiRequest<RoleAssignment>(`/admin/users/${id}/roles/${role}`, {
    method: "POST",
    body: { assignment_type },
  });
