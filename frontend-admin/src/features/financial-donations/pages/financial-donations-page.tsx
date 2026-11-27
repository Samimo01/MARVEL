import { useState } from "react";
import { PageHeading } from "@/components/shared/feature-page";
import { useFinancialDonations } from "@/features/financial-donations/hooks/use-financial-donations";
import DonationTable from "@/features/financial-donations/components/donation-table";
export default function FinancialDonationsPage() {
  const { rows, loading, error, generateReceipt, reload } =
    useFinancialDonations();
  const [message, setMessage] = useState("");
  const handleReceipt = async (id: string) => {
    try {
      const result = await generateReceipt(id);
      setMessage(result.message || "Reçu généré.");
      if (result.receipt_url)
        window.open(result.receipt_url, "_blank", "noopener,noreferrer");
    } catch (e) {
      setMessage(
        e instanceof Error ? e.message : "Impossible de générer le reçu.",
      );
    }
  };
  return (
    <div>
      <PageHeading
        title="Dons financiers"
        description="Consultez les dons monétaires et générez les reçus éligibles."
      />
      {message && (
        <p role="status" className="mb-4 text-sm text-brand-600">
          {message}
        </p>
      )}
      {error && (
        <p role="alert" className="mb-4 text-sm text-red-600">
          {error} <button onClick={reload}>Réessayer</button>
        </p>
      )}
      <DonationTable
        rows={rows}
        loading={loading}
        onReceipt={(id) => void handleReceipt(id)}
      />
    </div>
  );
}
