import { PageMeta } from "@/components/shared/page-meta";
import { Link } from "react-router";
export default function AccessDeniedPage() {
  return (
    <div className="mx-auto max-w-xl rounded-2xl border border-red-200 bg-white p-8 text-center dark:border-red-900/50 dark:bg-white/3">
      <PageMeta
        title="Accès refusé"
        description="Vous ne disposez pas des autorisations nécessaires."
      />
      <div className="mx-auto mb-4 flex size-12 items-center justify-center rounded-full bg-red-50 text-xl text-red-600 dark:bg-red-500/10">
        !
      </div>
      <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
        Accès refusé
      </h1>
      <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
        Votre compte ne possède pas les rôles nécessaires pour consulter cette
        page.
      </p>
      <Link
        to="/"
        className="mt-5 inline-flex rounded-lg bg-brand-500 px-4 py-2 text-sm font-medium text-white"
      >
        Retour au tableau de bord
      </Link>
    </div>
  );
}
