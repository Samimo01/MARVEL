import { PageHeading } from "@/components/shared/feature-page";
import { useReceipts } from "@/features/receipts/hooks/use-receipts";
import ReceiptTable from "@/features/receipts/components/receipt-table";
export default function ReceiptsPage() {
  const { data, loading } = useReceipts();
  return (
    <div>
      <PageHeading
        title="Reçus"
        description="Retrouvez les justificatifs des dons financiers."
      />
      <ReceiptTable rows={data ?? []} loading={loading} />
    </div>
  );
}
