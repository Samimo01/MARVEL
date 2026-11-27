import { useAsyncResource } from "@/hooks/use-async-resource";
import {
  closeCampaign,
  deleteCampaign,
  listCampaigns,
  publishCampaign,
} from "@/features/campaigns/api";
export function useCampaigns() {
  const resource = useAsyncResource(listCampaigns);
  const rows = (resource.data ?? []).map((campaign) => ({
    ...campaign,
    canPublish: campaign.status === "Draft",
    canClose: campaign.status !== "closed" && campaign.status !== "Invisible",
  }));
  return {
    ...resource,
    rows,
    publish: async (id: string) => {
      await publishCampaign(id);
      await resource.reload();
    },
    close: async (id: string) => {
      await closeCampaign(id);
      await resource.reload();
    },
    remove: async (id: string) => {
      await deleteCampaign(id);
      await resource.reload();
    },
  };
}
