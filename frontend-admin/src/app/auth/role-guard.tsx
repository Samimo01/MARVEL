import type { ReactNode } from "react";
import { Navigate } from "react-router";
import { useSession } from "@/app/auth/session-context";
import { hasAnyRole } from "@/app/auth/permissions";

export default function RoleGuard({
  roles,
  children,
}: {
  roles: string[];
  children: ReactNode;
}) {
  const session = useSession();
  if (!hasAnyRole(session.roles, roles))
    return <Navigate to="/access-denied" replace />;
  return children;
}
