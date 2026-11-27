import {
  PageHeading,
  DataPanel,
  StatusPill,
} from "@/components/shared/feature-page";
import { PageMeta } from "@/components/shared/page-meta";
import { useSession } from "@/app/auth/session-context";
import { ROLE } from "@/app/auth/permissions";
import { useDashboard } from "@/features/dashboard/hooks/use-dashboard";
import DonationChart from "@/features/dashboard/components/donation-chart";
import StatCard from "@/features/dashboard/components/stat-card";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
export default function DashboardPage() {
  const { data, loading } = useDashboard();
  const { roles, user } = useSession();
  const isTreasurer =
    roles.includes(ROLE.treasurer) || roles.includes(ROLE.administrator);
  const isCollection =
    roles.includes(ROLE.collection) || roles.includes(ROLE.administrator);
  const overview = data?.overview;
  return (
    <div className="min-w-0 space-y-6">
      <PageMeta
        title="Tableau de bord MARVEL"
        description="Vue d'ensemble des activités de l'association."
      />
      <PageHeading
        title={`Bonjour ${user.nickname || user.firstname},`}
        description="Voici un aperçu de l'activité de votre association."
      />
      <div className="grid min-w-0 grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {isTreasurer && (
          <StatCard
            label="Dons financiers"
            value={
              loading
                ? "—"
                : `${(overview?.financialTotal ?? 0).toLocaleString("fr-FR")} DA`
            }
            helper={`${overview?.financialDonations ?? 0} dons enregistrés`}
            icon="↗"
          />
        )}
        {isCollection && (
          <StatCard
            label="Dons en nature"
            value={loading ? "—" : String(overview?.naturalDeclarations ?? 0)}
            helper="Déclarations reçues"
            icon="▣"
          />
        )}
        <StatCard
          label="Campagnes actives"
          value={loading ? "—" : String(overview?.activeCampaigns ?? 0)}
          helper="Campagnes en cours"
          icon="◎"
        />
        <StatCard
          label="Actions à traiter"
          value={loading ? "—" : String(overview?.pendingActions ?? 0)}
          helper="Éléments en attente"
          icon="◷"
        />
      </div>
      <DonationChart
        financial={data?.financial ?? []}
        natural={data?.natural ?? []}
      />
      <div className="grid min-w-0 gap-6 xl:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)]">
        <div className="min-w-0">
          <DataPanel
            title="Activité récente"
            description="Derniers événements de démonstration"
            rows={
              (overview?.recentActivities ?? []) as unknown as Record<
                string,
                unknown
              >[]
            }
            columns={[
              {
                key: "label",
                label: "Activité",
                render: (row) => (
                  <div className="min-w-0">
                    <p className="break-words font-medium text-gray-800 dark:text-white">
                      {String(row.label)}
                    </p>
                    <p className="mt-1 break-words text-xs text-gray-400">
                      {String(row.detail)}
                    </p>
                  </div>
                ),
              },
              { key: "date", label: "Date" },
              {
                key: "status",
                label: "Statut",
                render: (row) => <StatusPill value={String(row.status)} />,
              },
            ]}
          />
        </div>
        <Card className="min-w-0">
          <CardHeader>
            <CardTitle>Accès rapide</CardTitle>
          </CardHeader>
          <CardContent className="grid min-w-0 gap-3 text-sm text-gray-600 dark:text-gray-300">
            <p>
              Utilisez le menu latéral pour accéder aux modules correspondant à
              vos rôles.
            </p>
            <div className="rounded-lg bg-brand-50 p-3 text-brand-700 dark:bg-brand-500/10 dark:text-brand-300">
              Les statistiques affichées ici sont provisoires : le backend ne
              fournit pas encore d’API Dashboard agrégée.
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
