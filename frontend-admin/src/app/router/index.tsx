import { Error404Page } from "@/features/errors";
import { DashboardPage } from "@/features/dashboard";
import { ProfilePage } from "@/features/profile";
import AdminLayout from "@/layouts/admin-layout";
import { Route, Routes } from "react-router";
import BackofficeGuard from "@/app/auth/backoffice-guard";

export default function AppRouter() {
  return (
    <BackofficeGuard>
      <Routes>
        <Route element={<AdminLayout />}>
          <Route index element={<DashboardPage />} />
          <Route path="/profile" element={<ProfilePage />} />
        </Route>

        <Route path="/error-404" element={<Error404Page />} />
        <Route path="*" element={<Error404Page />} />
      </Routes>
    </BackofficeGuard>
  );
}
