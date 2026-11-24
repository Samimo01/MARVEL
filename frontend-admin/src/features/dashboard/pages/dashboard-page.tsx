import { config } from "@/app/config";
import { PageMeta } from "@/components/shared/page-meta";
import { CheckCircleIcon } from "@/icons";

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <PageMeta
        title="Accueil du backoffice"
        description="Accueil temporaire du backoffice MARVEL."
      />

      <section className="overflow-hidden rounded-2xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-white/3">
        <div className="max-w-3xl p-6 lg:p-10">
          <div className="inline-flex items-center gap-2 rounded-full bg-green-50 px-3 py-1.5 text-sm font-medium text-green-700 dark:bg-green-500/10 dark:text-green-400">
            <CheckCircleIcon className="size-4" aria-hidden="true" />
            Accès au backoffice autorisé
          </div>
          <p className="mt-6 text-sm font-medium text-brand-600 dark:text-brand-400">
            Accueil temporaire
          </p>
          <h1 className="mt-2 text-2xl font-semibold text-gray-900 dark:text-white">
            Bienvenue dans le backoffice MARVEL
          </h1>
          <p className="mt-3 text-sm leading-6 text-gray-600 dark:text-gray-400">
            Votre session a été vérifiée et un rôle de gestion actif a été
            reconnu. Cette page temporaire vous permet de tester la connexion
            et la redirection depuis le site vitrine. Les modules de gestion
            seront intégrés progressivement.
          </p>
          <a
            href={config.publicUrl}
            className="mt-6 inline-flex min-h-10 items-center rounded-lg bg-brand-500 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-brand-600"
          >
            Retourner au site vitrine
          </a>
        </div>
      </section>
    </div>
  );
}
