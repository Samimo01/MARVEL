import { useState } from "react";
import { PageHeading } from "@/components/shared/feature-page";
import { useMissions } from "@/features/missions/hooks/use-missions";
import MissionTable from "@/features/missions/components/mission-table";
export default function MissionsPage() {
  const { rows, loading, error, publish, complete, cancel, reload } =
    useMissions();
  const [message, setMessage] = useState("");
  const run = async (fn: () => Promise<void>) => {
    try {
      await fn();
      setMessage("Mission mise à jour.");
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Erreur.");
    }
  };
  return (
    <div>
      <PageHeading
        title="Missions"
        description="Organisez les missions et suivez leur état de publication."
      />
      {message && <p className="mb-4 text-sm text-brand-600">{message}</p>}
      {error && (
        <p role="alert" className="mb-4 text-sm text-red-600">
          {error} <button onClick={reload}>Réessayer</button>
        </p>
      )}
      <MissionTable
        rows={rows}
        loading={loading}
        onPublish={(id) => void run(() => publish(id))}
        onComplete={(id) => {
          if (window.confirm("Marquer cette mission comme terminée ?"))
            void run(() => complete(id));
        }}
        onCancel={(id) => {
          if (window.confirm("Annuler cette mission ?"))
            void run(() => cancel(id));
        }}
      />
    </div>
  );
}
