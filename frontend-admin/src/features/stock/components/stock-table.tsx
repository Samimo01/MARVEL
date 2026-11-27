import { DataPanel, type Column } from "@/components/shared/feature-page";
type Item = {
  id: string;
  name: string;
  category: string;
  quantity: number;
  unit: string;
  status: string;
};
export default function StockTable({
  rows,
  loading,
}: {
  rows: Item[];
  loading: boolean;
}) {
  const columns: Column<Item>[] = [
    { key: "name", label: "Article" },
    { key: "category", label: "Catégorie" },
    {
      key: "quantity",
      label: "Quantité",
      render: (r) => (
        <strong>
          {r.quantity} {r.unit}
        </strong>
      ),
    },
    { key: "status", label: "État" },
  ];
  return (
    <DataPanel
      title="État du stock"
      description="Données de démonstration — API stock à développer"
      badge="Mode démo"
      rows={rows}
      columns={columns}
      loading={loading}
    />
  );
}
