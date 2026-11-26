import { useState } from "react";
import { PageHeading } from "@/components/shared/feature-page";
import { useNaturalDonations } from "@/features/natural-donations/hooks/use-natural-donations";
import NaturalDonationTable from "@/features/natural-donations/components/natural-donation-table";
export default function NaturalDonationsPage() {
  const { rows, loading, error, validate, reject, stockIn, reload } =
    useNaturalDonations();
  const [message, setMessage] = useState("");
  const run = async (fn: () => Promise<void>) => {
    try {
      await fn();
      setMessage("Opération enregistrée.");
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Erreur.");
    }
  };
  return (
    <div>
      <PageHeading
        title="Dons en nature"
        description="Validez les déclarations, organisez leur réception et suivez les entrées en stock."
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
      <NaturalDonationTable
        rows={rows}
        loading={loading}
        onValidate={(id) => void run(() => validate(id))}
        onReject={(id) => {
          const reason = window.prompt(
            "Motif du refus (5 caractères minimum) :",
          );
          if (reason) void run(() => reject(id, reason));
        }}
        onStockIn={(id) => {
          if (
            window.confirm(
              "Confirmer l'entrée en stock des articles conformes ?",
            )
          )
            void run(() => stockIn(id));
        }}
      />
    </div>
  );
}
