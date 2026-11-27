import { useEffect, useState } from "react";
import { PageHeading } from "@/components/shared/feature-page";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useUserRoles } from "@/features/users/hooks/use-user-roles";
import UserRolePanel from "@/features/users/components/user-role-panel";
export default function UsersPage() {
  const {
    roles,
    assignments,
    activeRoles,
    loading,
    error,
    loadRoles,
    search,
    update,
  } = useUserRoles();
  const [id, setId] = useState("");
  const [message, setMessage] = useState("");
  useEffect(() => {
    void loadRoles();
  }, [loadRoles]);
  const lookup = async () => {
    try {
      await search(id.trim());
    } catch {
      // L'erreur est déjà exposée par useUserRoles.
    }
  };
  const change = async (role: string, type: "assigned" | "revoked") => {
    if (type === "revoked" && !window.confirm(`Révoquer le rôle ${role} ?`))
      return;
    try {
      await update(role, type);
      setMessage("Attribution mise à jour.");
    } catch (e) {
      setMessage(
        e instanceof Error ? e.message : "Erreur lors de la mise à jour.",
      );
    }
  };
  return (
    <div>
      <PageHeading
        title="Utilisateurs et rôles"
        description="Attribuez les rôles aux comptes existants."
      />
      <div className="mb-6 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800 dark:border-amber-500/20 dark:bg-amber-500/10 dark:text-amber-200">
        Le backend ne fournit pas encore de route de recherche ou de liste des
        utilisateurs. Saisissez l'identifiant UUID d'un compte connu pour
        consulter ses rôles.
      </div>
      <div className="mb-5 flex max-w-2xl gap-2">
        <Input
          value={id}
          onChange={(e) => setId(e.target.value)}
          placeholder="UUID de l'utilisateur"
        />
        <Button onClick={() => void lookup()} disabled={!id.trim() || loading}>
          Consulter
        </Button>
      </div>
      {message && <p className="mb-3 text-sm text-brand-600">{message}</p>}
      {error && (
        <p role="alert" className="mb-3 text-sm text-red-600">
          {error}
        </p>
      )}
      {assignments.length > 0 && (
        <p className="mb-3 text-xs text-gray-500">
          Rôles consultés : {assignments.length}
        </p>
      )}
      {roles.length > 0 && (
        <UserRolePanel
          roles={roles}
          activeRoles={activeRoles}
          loading={loading}
          onUpdate={(role, type) => void change(role, type)}
        />
      )}
    </div>
  );
}