import { Route, Routes } from "react-router";
import BackofficeGuard from "@/app/auth/backoffice-guard";
import RoleGuard from "@/app/auth/role-guard";
import { PAGE_PERMISSIONS } from "@/app/auth/permissions";
import AdminLayout from "@/layouts/admin-layout";
import { DashboardPage } from "@/features/dashboard";
import { ProfilePage } from "@/features/profile";
import { Error404Page } from "@/features/errors";
import AccessDeniedPage from "@/components/shared/feedback/access-denied";
import { CampaignsPage } from "@/features/campaigns";
import { FinancialDonationsPage } from "@/features/financial-donations";
import { NaturalDonationsPage } from "@/features/natural-donations";
import { CollectsPage } from "@/features/collects";
import { TreasuryPage } from "@/features/treasury";
import { MissionsPage } from "@/features/missions";
import { StockPage } from "@/features/stock";
import { ReceiptsPage } from "@/features/receipts";
import { BeneficiariesPage } from "@/features/beneficiaries";
import { DistributionsPage } from "@/features/distributions";
import { UsersPage } from "@/features/users";
import { LoginPage } from "@/features/auth";

export default function AppRouter() {
  return (
    <Routes>
      {/* Public route: it must remain reachable without an active session. */}
      <Route path="/login" element={<LoginPage />} />

      {/* All back-office pages require an authenticated management role. */}
      <Route
        path="/"
        element={
          <BackofficeGuard>
            <AdminLayout />
          </BackofficeGuard>
        }
      >
        <Route
          index
          element={
            <RoleGuard roles={PAGE_PERMISSIONS.dashboard}>
              <DashboardPage />
            </RoleGuard>
          }
        />
        <Route
          path="profile"
          element={
            <RoleGuard roles={PAGE_PERMISSIONS.profile}>
              <ProfilePage />
            </RoleGuard>
          }
        />
        <Route
          path="campaigns"
          element={
            <RoleGuard roles={PAGE_PERMISSIONS.campaigns}>
              <CampaignsPage />
            </RoleGuard>
          }
        />
        <Route
          path="financial-donations"
          element={
            <RoleGuard roles={PAGE_PERMISSIONS.financialDonations}>
              <FinancialDonationsPage />
            </RoleGuard>
          }
        />
        <Route
          path="natural-donations"
          element={
            <RoleGuard roles={PAGE_PERMISSIONS.naturalDonations}>
              <NaturalDonationsPage />
            </RoleGuard>
          }
        />
        <Route
          path="collects"
          element={
            <RoleGuard roles={PAGE_PERMISSIONS.collects}>
              <CollectsPage />
            </RoleGuard>
          }
        />
        <Route
          path="stock"
          element={
            <RoleGuard roles={PAGE_PERMISSIONS.stock}>
              <StockPage />
            </RoleGuard>
          }
        />
        <Route
          path="treasury"
          element={
            <RoleGuard roles={PAGE_PERMISSIONS.treasury}>
              <TreasuryPage />
            </RoleGuard>
          }
        />
        <Route
          path="receipts"
          element={
            <RoleGuard roles={PAGE_PERMISSIONS.receipts}>
              <ReceiptsPage />
            </RoleGuard>
          }
        />
        <Route
          path="beneficiaries"
          element={
            <RoleGuard roles={PAGE_PERMISSIONS.beneficiaries}>
              <BeneficiariesPage />
            </RoleGuard>
          }
        />
        <Route
          path="distributions"
          element={
            <RoleGuard roles={PAGE_PERMISSIONS.distributions}>
              <DistributionsPage />
            </RoleGuard>
          }
        />
        <Route
          path="missions"
          element={
            <RoleGuard roles={PAGE_PERMISSIONS.missions}>
              <MissionsPage />
            </RoleGuard>
          }
        />
        <Route
          path="users"
          element={
            <RoleGuard roles={PAGE_PERMISSIONS.users}>
              <UsersPage />
            </RoleGuard>
          }
        />
        <Route path="access-denied" element={<AccessDeniedPage />} />
        <Route path="error-404" element={<Error404Page />} />
        <Route path="*" element={<Error404Page />} />
      </Route>
    </Routes>
  );
}
