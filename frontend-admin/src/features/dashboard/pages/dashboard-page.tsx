import { PageMeta } from "@/components/shared/page-meta";

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <PageMeta
        title="Tableau de bord"
        description="Espace d'administration de la plateforme."
      />

      <div className="rounded-2xl border border-gray-200 bg-white p-6 dark:border-gray-800 dark:bg-white/3 lg:p-8">
        <div className="max-w-2xl">
          <p className="text-sm font-medium text-brand-600 dark:text-brand-400">
            Administration
          </p>
          <h1 className="mt-2 text-2xl font-semibold text-gray-900 dark:text-white">
            Bienvenue dans votre espace d'administration
          </h1>
          <p className="mt-3 text-sm leading-6 text-gray-600 dark:text-gray-400">
            Le socle de l'espace administrateur est prêt. Les modules de gestion
            des dons, des demandes d'aide, des stocks, des distributions et des
            bénévoles seront intégrés progressivement.
          </p>
        </div>
      </div>
    </div>
  );
}
