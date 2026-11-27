import { useState } from "react";
import { ApiError } from "@/app/api-client";
import { BACKOFFICE_ROLES, hasAnyRole } from "@/app/auth/permissions";
import { getCurrentSession, login, logout } from "@/features/auth/api";
import type { LoginPayload } from "@/features/auth/types";

export function useLogin() {
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");

  const signIn = async (payload: LoginPayload) => {
    setPending(true);
    setError("");

    try {
      await login(payload);

      // The login endpoint sets an HttpOnly cookie; the session is then
      // retrieved separately to verify that this account may use the back-office.
      const session = await getCurrentSession();
      if (!hasAnyRole(session.roles ?? [], BACKOFFICE_ROLES)) {
        let sessionClosed = true;
        try {
          await logout();
        } catch {
          sessionClosed = false;
        }

        setError(
          sessionClosed
            ? "Votre compte est valide, mais il ne possède aucun rôle autorisé à accéder au back-office."
            : "Votre compte ne possède aucun rôle autorisé pour le back-office et la fermeture de session a échoué. Contactez un administrateur avant de réessayer.",
        );
        return false;
      }

      return true;
    } catch (caught) {
      if (caught instanceof ApiError && caught.status === 422) {
        setError(
          "Veuillez saisir une adresse e-mail valide et un mot de passe.",
        );
      } else if (caught instanceof ApiError && caught.status === 401) {
        setError("Adresse e-mail ou mot de passe incorrect.");
      } else {
        setError(
          caught instanceof Error
            ? caught.message
            : "La connexion est momentanément impossible. Veuillez réessayer.",
        );
      }
      return false;
    } finally {
      setPending(false);
    }
  };

  return { pending, error, signIn };
}
