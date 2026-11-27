import { DataPanel, type Column } from "@/components/shared/feature-page";
type Row = {
  id: string;
  beneficiary: string;
  date: string;
  items: string;
  status: string;
};
export default function DistributionTable({
  rows,
  loading,
}: {
  rows: Row[];
  loading: boolean;
}) {
  const columns: Column<Row>[] = [
    { key: "id", label: "Référence" },
    { key: "beneficiary", label: "Bénéficiaire" },
    { key: "date", label: "Date" },
    { key: "items", label: "Articles" },
    { key: "status", label: "Statut" },
  ];
  return (
    <DataPanel
      title="Distributions"
      description="Données de démonstration — module backend non disponible"
      badge="Mode démo"
      rows={rows}
      columns={columns}
      loading={loading}
    />
  );
}
