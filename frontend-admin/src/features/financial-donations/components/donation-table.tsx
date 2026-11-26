import {
  DataPanel,
  StatusPill,
  type Column,
} from "@/components/shared/feature-page";
import type { FinancialDonation } from "@/features/financial-donations/types";
type DonationRow = FinancialDonation & { canGenerateReceipt: boolean };
export default function DonationTable({
  rows,
  loading,
  onReceipt,
}: {
  rows: DonationRow[];
  loading: boolean;
  onReceipt: (id: string) => void;
}) {
  const columns: Column<DonationRow>[] = [
    {
      key: "id_don_f",
      label: "Référence",
      render: (r) => (
        <span className="font-mono text-xs">{r.id_don_f.slice(0, 8)}…</span>
      ),
    },
    {
      key: "amount",
      label: "Montant",
      render: (r) => (
        <strong>{Number(r.amount).toLocaleString("fr-FR")} DA</strong>
      ),
    },
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
      key: "is_anonymous",
      label: "Donateur",
      render: (r) => (r.is_anonymous ? "Anonyme" : "Identifié"),
    },
    {
      key: "actions",
      label: "Reçu",
      render: (r) => (
        <button
          disabled={!r.canGenerateReceipt}
          onClick={() => onReceipt(r.id_don_f)}
          className="text-xs font-medium text-brand-600 disabled:text-gray-300"
        >
          Générer
        </button>
      ),
    },
  ];
  return (
    <DataPanel
      title="Dons financiers"
      description="Dons enregistrés dans le backend"
      rows={rows}
      columns={columns}
      loading={loading}
    />
  );
}
