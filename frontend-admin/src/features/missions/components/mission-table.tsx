import {
  DataPanel,
  StatusPill,
  type Column,
} from "@/components/shared/feature-page";
import type { Mission } from "@/features/missions/types";
type MissionRow = Mission & {
  canPublish: boolean;
  canComplete: boolean;
  canCancel: boolean;
};
export default function MissionTable({
  rows,
  loading,
  onPublish,
  onComplete,
  onCancel,
}: {
  rows: MissionRow[];
  loading: boolean;
  onPublish: (id: string) => void;
  onComplete: (id: string) => void;
  onCancel: (id: string) => void;
}) {
  const columns: Column<MissionRow>[] = [
    {
      key: "title",
      label: "Mission",
      render: (r) => (
        <div>
          <p className="font-medium">{r.title}</p>
          <p className="text-xs text-gray-400">
            {r.place ?? "Lieu à confirmer"}
          </p>
        </div>
      ),
    },
    {
      key: "start_at",
      label: "Début",
      render: (r) =>
        r.start_at
          ? new Date(r.start_at).toLocaleString("fr-FR")
          : "À planifier",
    },
    {
      key: "seat_number",
      label: "Places",
      render: (r) => r.seat_number ?? "—",
    },
    {
      key: "status",
      label: "Statut",
      render: (r) => <StatusPill value={r.status} />,
    },
    {
      key: "actions",
      label: "Actions",
      render: (r) => (
        <div className="flex gap-2">
          {r.canPublish && (
            <button
              className="text-xs text-brand-600"
              onClick={() => onPublish(r.id_mission)}
            >
              Publier
            </button>
          )}
          {r.canComplete && r.canCancel && (
            <>
              <button
                className="text-xs text-green-600"
                onClick={() => onComplete(r.id_mission)}
              >
                Terminer
              </button>
              <button
                className="text-xs text-red-600"
                onClick={() => onCancel(r.id_mission)}
              >
                Annuler
              </button>
            </>
          )}
        </div>
      ),
    },
  ];
  return (
    <DataPanel
      title="Missions"
      rows={rows}
      columns={columns}
      loading={loading}
    />
  );
}
