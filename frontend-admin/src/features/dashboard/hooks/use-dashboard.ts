import { useEffect, useState } from "react";
import {
  getDashboardOverview,
  getFinancialDonationTrend,
  getNaturalDonationBreakdown,
} from "@/features/dashboard/api";
export function useDashboard() {
  const [data, setData] = useState<{
    overview: Awaited<ReturnType<typeof getDashboardOverview>>;
    financial: Awaited<ReturnType<typeof getFinancialDonationTrend>>;
    natural: Awaited<ReturnType<typeof getNaturalDonationBreakdown>>;
  } | null>(null);
  useEffect(() => {
    let active = true;
    void Promise.all([
      getDashboardOverview(),
      getFinancialDonationTrend(),
      getNaturalDonationBreakdown(),
    ])
      .then(([overview, financial, natural]) => {
        if (active) setData({ overview, financial, natural });
      })
      .catch((caught: unknown) => {
        console.error("Erreur lors du chargement du tableau de bord.", caught);
      });
    return () => {
      active = false;
    };
  }, []);
  return { data, loading: !data };
}
