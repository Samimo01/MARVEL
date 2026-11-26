import { DataPanel, type Column } from "@/components/shared/feature-page";
type Row = {
  id: string;
  name: string;
  area: string;
  status: string;
  lastAid: string;
};
export default function BeneficiaryTable({
  rows,
  loading,
}: {
  rows: Row[];
  loading: boolean;
}) {
  const columns: Column<Row>[] = [
    { key: "id", label: "Référence" },
    { key: "name", label: "Dossier" },
    { key: "area", label: "Localité" },
    { key: "status", label: "Statut" },
    { key: "lastAid", label: "Dernière aide" },
  ];
  return (
    <DataPanel
      title="Bénéficiaires"
      description="Données de démonstration — module backend non disponible"
      badge="Mode démo"
      rows={rows}
      columns={columns}
      loading={loading}
    />
  );
}
