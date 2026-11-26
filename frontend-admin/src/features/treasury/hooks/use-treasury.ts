import { useAsyncResource } from "@/hooks/use-async-resource";
import {
  getBudgetSummary,
  listFunds,
  exportTreasury,
} from "@/features/treasury/api";
export function useTreasury() {
  const budget = useAsyncResource(getBudgetSummary);
  const funds = useAsyncResource(listFunds);
  return {
    budget: budget.data,
    funds: funds.data,
    loading: budget.loading || funds.loading,
    error: budget.error || funds.error,
    reload: () => Promise.all([budget.reload(), funds.reload()]),
    export: exportTreasury,
  };
}
