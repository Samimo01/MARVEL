import {
  dashboardOverview,
  financialTrend,
  naturalCategories,
} from "@/features/dashboard/mocks/dashboard-data";
export const getDashboardOverview = async () => dashboardOverview;
export const getFinancialDonationTrend = async () => financialTrend;
export const getNaturalDonationBreakdown = async () => naturalCategories;
