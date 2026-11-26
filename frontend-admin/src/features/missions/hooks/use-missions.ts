import { useAsyncResource } from "@/hooks/use-async-resource";
import {
  listMissions,
  publishMission,
  cancelMission,
  completeMission,
} from "@/features/missions/api";
export function useMissions() {
  const resource = useAsyncResource(listMissions);
  const rows = (resource.data ?? []).map((mission) => ({
    ...mission,
    canPublish: mission.status === "Draft",
    canComplete: mission.status === "Publish",
    canCancel: mission.status === "Publish",
  }));
  return {
    ...resource,
    rows,
    publish: async (id: string) => {
      await publishMission(id);
      await resource.reload();
    },
    cancel: async (id: string) => {
      await cancelMission(id);
      await resource.reload();
    },
    complete: async (id: string) => {
      await completeMission(id);
      await resource.reload();
    },
  };
}
