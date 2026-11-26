import { useAsyncResource } from "@/hooks/use-async-resource";
import { useSession } from "@/app/auth/session-context";
import { ROLE } from "@/app/auth/permissions";
import { confirmCollect, listCollects } from "@/features/collects/api";
export function useCollects() {
  const resource = useAsyncResource(listCollects);
  const { roles } = useSession();
  const canConfirm =
    roles.includes(ROLE.stock) || roles.includes(ROLE.administrator);
  const rows = (resource.data ?? []).map((collect) => ({
    ...collect,
    canConfirm: canConfirm && collect.status === "Planned",
  }));
  return {
    ...resource,
    rows,
    confirm: async (id: string) => {
      await confirmCollect(id);
      await resource.reload();
    },
  };
}
