import AppLayout from "@/components/layout/app-layout";
import DashboardPage from "@/pages/main/dashboard";
import { Error404Page } from "@/pages/main/pages";
import ProfilePage from "@/pages/main/profile";
import { Route, Routes } from "react-router";

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<DashboardPage />} />
        <Route path="/profile" element={<ProfilePage />} />
      </Route>

      {/* Full-width / Error / Status Pages */}
      <Route path="/error-404" element={<Error404Page />} />

      {/* Fallback Route */}
      <Route path="*" element={<Error404Page />} />
    </Routes>
  );
}
