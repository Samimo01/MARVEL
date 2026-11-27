import { useState } from "react";
import { PageHeading } from "@/components/shared/feature-page";
import { useCollects } from "@/features/collects/hooks/use-collects";
import CollectTable from "@/features/collects/components/collect-table";

export default function CollectsPage() {
  const { rows, loading, error, confirm, reload } = useCollects();
  const [message, setMessage] = useState("");

  const handle = async (id: string) => {
    if (!window.confirm("Confirmer la réception de cette collecte ?")) {
      return;
    }

    try {
      await confirm(id);
      setMessage("Collecte confirmée.");
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Erreur.");
    }
  };

  return (
    <div>
      <PageHeading
        title="Collectes"
        description="Consultez les collectes planifiées et confirmez leur réception."
      />

      {message && <p className="mb-4 text-sm text-brand-600">{message}</p>}

      {error && (
        <p role="alert" className="mb-4 text-sm text-red-600">
          {error} <button onClick={reload}>Réessayer</button>
        </p>
      )}

      <CollectTable
        rows={rows}
        loading={loading}
        onConfirm={(id) => void handle(id)}
      />
    </div>
  );
}
