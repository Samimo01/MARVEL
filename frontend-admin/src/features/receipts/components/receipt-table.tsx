import { DataPanel, type Column } from "@/components/shared/feature-page";
type Row = {
  id: string;
  donor: string;
  amount: string;
  date: string;
  status: string;
};
export default function ReceiptTable({
  rows,
  loading,
}: {
  rows: Row[];
  loading: boolean;
}) {
  const columns: Column<Row>[] = [
    { key: "id", label: "Référence" },
    { key: "donor", label: "Donateur" },
    { key: "amount", label: "Montant" },
    { key: "date", label: "Date" },
    { key: "status", label: "Statut" },
  ];
  return (
    <DataPanel
      title="Reçus"
      description="Aperçu de démonstration — le backend ne fournit pas encore de liste des reçus"
      badge="Mode démo"
      rows={rows}
      columns={columns}
      loading={loading}
    />
  );
}
