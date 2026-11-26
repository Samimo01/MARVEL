import { useState } from "react";
import { PageHeading } from "@/components/shared/feature-page";
import { useCampaigns } from "@/features/campaigns/hooks/use-campaigns";
import CampaignTable from "@/features/campaigns/components/campaign-table";
import { Button } from "@/components/ui/button";
export default function CampaignsPage() {
  const { rows, loading, error, publish, close, reload } = useCampaigns();
  const [message, setMessage] = useState("");
  const run = async (action: () => Promise<void>) => {
    try {
      await action();
      setMessage("Opération enregistrée.");
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Erreur.");
    }
  };
  return (
    <div>
      <PageHeading
        title="Campagnes"
        description="Créez, publiez et suivez les campagnes de collecte."
        action={
          <Button
            onClick={() =>
              setMessage(
                "La création est disponible via l'API, mais le formulaire détaillé sera ajouté dans une prochaine étape.",
              )
            }
          >
            Nouvelle campagne
          </Button>
        }
      />
      {error && (
        <p role="alert" className="mb-4 text-sm text-red-600">
          {error} <button onClick={reload}>Réessayer</button>
        </p>
      )}
      {message && (
        <p role="status" className="mb-4 text-sm text-brand-600">
          {message}
        </p>
      )}
      <CampaignTable
        rows={rows}
        loading={loading}
        onPublish={(id) => void run(() => publish(id))}
        onClose={(id) => {
          if (window.confirm("Clôturer cette campagne ?"))
            void run(() => close(id));
        }}
      />
    </div>
  );
}
