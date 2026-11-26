import {
  DataPanel,
  StatusPill,
  type Column,
} from "@/components/shared/feature-page";
import type { NaturalDonation } from "@/features/natural-donations/types";
type NaturalDonationRow = NaturalDonation & {
  canValidate: boolean;
  canReject: boolean;
  canStockIn: boolean;
};
export default function NaturalDonationTable({
  rows,
  loading,
  onValidate,
  onReject,
  onStockIn,
}: {
  rows: NaturalDonationRow[];
  loading: boolean;
  onValidate: (id: string) => void;
  onReject: (id: string) => void;
  onStockIn: (id: string) => void;
}) {
  const columns: Column<NaturalDonationRow>[] = [
    {
      key: "id_don_n",
      label: "Référence",
      render: (r) => (
        <span className="font-mono text-xs">{r.id_don_n.slice(0, 8)}…</span>
      ),
    },
    { key: "recovery_mode", label: "Mode de réception" },
    { key: "collection_address", label: "Adresse" },
    {
      key: "created_at",
      label: "Date",
      render: (r) => new Date(r.created_at).toLocaleDateString("fr-FR"),
    },
    {
      key: "status",
      label: "Statut",
      render: (r) => <StatusPill value={r.status} />,
    },
    {
      key: "actions",
      label: "Actions",
      render: (r) => (
        <div className="flex flex-wrap gap-2">
          {r.canValidate && (
            <>
              <button
                className="text-xs text-green-600"
                onClick={() => onValidate(r.id_don_n)}
              >
                Valider
              </button>
            </>
          )}
          {r.canReject && (
            <button
              className="text-xs text-red-600"
              onClick={() => onReject(r.id_don_n)}
            >
              Refuser
            </button>
          )}
          {r.canStockIn && (
            <button
              className="text-xs text-brand-600"
              onClick={() => onStockIn(r.id_don_n)}
            >
              Entrée en stock
            </button>
          )}
        </div>
      ),
    },
  ];
  return (
    <DataPanel
      title="Déclarations de dons en nature"
      description="Validez les dons et suivez leur réception"
      rows={rows}
      columns={columns}
      loading={loading}
    />
  );
}
