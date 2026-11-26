import {
  DataPanel,
  StatusPill,
  type Column,
} from "@/components/shared/feature-page";
import type { Campaign } from "@/features/campaigns/types";

type CampaignRow = Campaign & {
  canPublish: boolean;
  canClose: boolean;
};

export default function CampaignTable({
  rows,
  loading,
  onPublish,
  onClose,
}: {
  rows: CampaignRow[];
  loading: boolean;
  onPublish: (id: string) => void;
  onClose: (id: string) => void;
}) {
  const columns: Column<CampaignRow>[] = [
    {
      key: "title",
      label: "Campagne",
      render: (row) => (
        <div>
          <p className="font-medium text-gray-800 dark:text-white">
            {row.title}
          </p>
          <p className="max-w-sm truncate text-xs text-gray-400">
            {row.description}
          </p>
        </div>
      ),
    },
    {
      key: "goal",
      label: "Objectif",
      render: (row) =>
        row.goal ? `${Number(row.goal).toLocaleString("fr-FR")} DA` : "—",
    },
    {
      key: "status",
      label: "Statut",
      render: (row) => <StatusPill value={row.status} />,
    },
    {
      key: "actions",
      label: "Actions",
      render: (row) => (
        <div className="flex gap-2">
          {row.canPublish && (
            <button
              className="text-xs font-medium text-brand-600"
              onClick={() => onPublish(row.id_campaign)}
            >
              Publier
            </button>
          )}

          {row.canClose && (
            <button
              className="text-xs font-medium text-red-600"
              onClick={() => onClose(row.id_campaign)}
            >
              Clôturer
            </button>
          )}
        </div>
      ),
    },
  ];

  return (
    <DataPanel
      title="Toutes les campagnes"
      description="Campagnes accessibles à votre rôle"
      rows={rows}
      columns={columns}
      loading={loading}
    />
  );
}
