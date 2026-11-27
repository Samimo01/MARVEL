export type RoleAssignment = {
  id_role_assignment: string;
  id_user: string;
  id_role: string;
  role_name: string;
  assignment_type: "assigned" | "revoked";
  created_at: string;
};
