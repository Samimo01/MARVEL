import { useState } from "react";
import {
  PageHeading,
  DataPanel,
  type Column,
} from "@/components/shared/feature-page";
import { Button } from "@/components/ui/button";
import { useTreasury } from "@/features/treasury/hooks/use-treasury";
import BudgetCards from "@/features/treasury/components/budget-cards";
import type { Fund } from "@/features/treasury/types";
export default function TreasuryPage() {
  const {
    budget,
    funds,
    loading,
    error,
    reload,
    export: download,
  } = useTreasury();
  const [message, setMessage] = useState("");
  const columns: Column<Fund>[] = [
    {
      key: "transaction_at",
      label: "Date",
      render: (r) => new Date(r.transaction_at).toLocaleDateString("fr-FR"),
    },
    { key: "category", label: "Catégorie" },
    {
      key: "amount",
      label: "Montant",
      render: (r) => `${Number(r.amount).toLocaleString("fr-FR")} DA`,
    },
    { key: "justificative", label: "Justificatif" },
  ];
  return (
    <div>
      <PageHeading
        title="Trésorerie"
        description="Suivez les recettes, les dépenses et le solde de l'association."
        action={
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => void download("csv")}>
              Exporter CSV
            </Button>
            <Button
              onClick={() =>
                setMessage(
                  "La création d'une dépense nécessite un événement associé (id_event) fourni par l'API.",
                )
              }
            >
              Nouvelle dépense
            </Button>
          </div>
        }
      />
      {message && <p className="mb-4 text-sm text-brand-600">{message}</p>}
      {error && (
        <p role="alert" className="mb-4 text-sm text-red-600">
          {error} <button onClick={reload}>Réessayer</button>
        </p>
      )}
      {budget && <BudgetCards budget={budget} />}
      <DataPanel
        title="Opérations financières"
        description="Opérations renvoyées par l'API"
        rows={funds ?? []}
        columns={columns}
        loading={loading}
      />
    </div>
  );
}
