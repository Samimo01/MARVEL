import {
  DataPanel,
  StatusPill,
  type Column,
} from "@/components/shared/feature-page";
import type { Collect } from "@/features/collects/types";
type CollectRow = Collect & { canConfirm: boolean };
export default function CollectTable({
  rows,
  loading,
  onConfirm,
}: {
  rows: CollectRow[];
  loading: boolean;
  onConfirm: (id: string) => void;
}) {
  const columns: Column<CollectRow>[] = [
    { key: "place", label: "Lieu" },
    {
      key: "planned_at",
      label: "Date prévue",
      render: (r) => new Date(r.planned_at).toLocaleString("fr-FR"),
    },
    {
      key: "status",
      label: "Statut",
      render: (r) => <StatusPill value={r.status} />,
    },
    {
      key: "actions",
      label: "Actions",
      render: (r) =>
        r.canConfirm ? (
          <button
            className="text-xs font-medium text-brand-600"
            onClick={() => onConfirm(r.id_collect)}
          >
            Confirmer la collecte
          </button>
        ) : (
          "—"
        ),
    },
  ];
  return (
    <DataPanel
      title="Collectes planifiées"
      rows={rows}
      columns={columns}
      loading={loading}
    />
  );
}
