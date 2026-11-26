import { PageHeading } from "@/components/shared/feature-page";
import { useStock } from "@/features/stock/hooks/use-stock";
import StockTable from "@/features/stock/components/stock-table";
export default function StockPage() {
  const { data, loading } = useStock();
  return (
    <div>
      <PageHeading
        title="Stock"
        description="Consultez les quantités disponibles par catégorie."
      />
      <StockTable rows={data ?? []} loading={loading} />
    </div>
  );
}
