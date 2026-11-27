import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
export default function UserRolePanel({
  roles,
  activeRoles,
  loading,
  onUpdate,
}: {
  roles: string[];
  activeRoles: string[];
  loading: boolean;
  onUpdate: (role: string, type: "assigned" | "revoked") => void;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Rôles du compte</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {roles.map((role) => {
          const active = activeRoles.includes(role);
          return (
            <div
              key={role}
              className="flex flex-wrap items-center justify-between gap-3 border-b border-gray-100 pb-3 last:border-0 dark:border-gray-800"
            >
              <div>
                <p className="text-sm font-medium text-gray-800 dark:text-white">
                  {role}
                </p>
                <p className="text-xs text-gray-400">
                  {active ? "Actif" : "Non attribué"}
                </p>
              </div>
              <Button
                size="sm"
                variant={active ? "destructive" : "outline"}
                disabled={loading}
                onClick={() => onUpdate(role, active ? "revoked" : "assigned")}
              >
                {active ? "Révoquer" : "Attribuer"}
              </Button>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
