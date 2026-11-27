import { useCallback, useState } from "react";
import {
  listRoles,
  listUserRoleAssignments,
  setUserRole,
} from "@/features/users/api";
import type { RoleAssignment } from "@/features/users/types";

export function useUserRoles() {
  const [roles, setRoles] = useState<string[]>([]);
  const [assignments, setAssignments] = useState<RoleAssignment[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [lookupId, setLookupId] = useState("");

  const loadRoles = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setRoles(await listRoles());
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Erreur.");
    } finally {
      setLoading(false);
    }
  }, []);

  const search = useCallback(async (id: string) => {
    setLookupId(id);
    setLoading(true);
    setError("");
    try {
      setAssignments(await listUserRoleAssignments(id));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Erreur.");
    } finally {
      setLoading(false);
    }
  }, []);

  const update = useCallback(
    async (role: string, type: "assigned" | "revoked") => {
      await setUserRole(lookupId, role, type);
      await search(lookupId);
    },
    [lookupId, search],
  );

  const latestAssignments = Object.values(
    assignments.reduce<Record<string, RoleAssignment>>((latest, assignment) => {
      const current = latest[assignment.role_name];
      if (
        !current ||
        new Date(assignment.created_at) > new Date(current.created_at)
      )
        latest[assignment.role_name] = assignment;
      return latest;
    }, {}),
  );
  const activeRoles = latestAssignments
    .filter((assignment) => assignment.assignment_type === "assigned")
    .map((assignment) => assignment.role_name);

  return {
    roles,
    assignments,
    activeRoles,
    loading,
    error,
    lookupId,
    loadRoles,
    search,
    update,
  };
}
