import { useEffect, useState, type ReactNode } from "react";
import { config } from "@/app/config";
import { BACKOFFICE_ROLES, hasAnyRole } from "@/app/auth/permissions";
import { SessionProvider, type UserSession } from "@/app/auth/session-context";
import { getCurrentSession } from "@/features/auth/api";

export default function BackofficeGuard({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<UserSession | null>(null);
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();

    getCurrentSession(controller.signal)
      .then((current) => {
        if (!hasAnyRole(current.roles ?? [], BACKOFFICE_ROLES)) {
          window.location.replace(config.publicUrl.replace(/\/+$/, ""));
          return;
        }
        setSession(current);
      })
      .catch((caught: unknown) => {
        if (caught instanceof Error && caught.name === "AbortError") return;

        if (
          typeof caught === "object" &&
          caught !== null &&
          "status" in caught &&
          (caught as { status: number }).status === 401
        ) {
          window.location.replace("/login");
          return;
        }

        setError(
          caught instanceof Error
            ? caught.message
            : "Impossible de vérifier les accès.",
        );
      });

    return () => controller.abort();
  }, [attempt]);

  if (error) {
    return (
      <main className="flex min-h-screen items-center justify-center p-6">
        <div className="max-w-md space-y-4 text-center">
          <p role="alert" className="text-sm text-red-600">
            {error}
          </p>
          <button
            className="rounded-lg bg-brand-500 px-4 py-2 text-sm font-medium text-white"
            onClick={() => {
              setError("");
              setAttempt((value) => value + 1);
            }}
          >
            Réessayer
          </button>
        </div>
      </main>
    );
  }

  if (!session) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p role="status" className="text-sm text-gray-500">
          Vérification des accès au back-office…
        </p>
      </main>
    );
  }

  return <SessionProvider session={session}>{children}</SessionProvider>;
}
