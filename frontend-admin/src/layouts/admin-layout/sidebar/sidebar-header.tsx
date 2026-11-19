import { SidebarHeader } from "@/components/ui/sidebar";
import { Link } from "react-router";
import logo from "@/assets/images/logo/logo.svg";
import logoDark from "@/assets/images/logo/logo-dark.svg";
import logoIcon from "@/assets/images/logo/logo-icon.svg";

interface AppSidebarHeaderProps {
  showContent: boolean;
}

export default function AppSidebarHeader({
  showContent,
}: AppSidebarHeaderProps) {
  return (
    <SidebarHeader className="px-5 py-8">
      <Link to="/">
        {showContent ? (
          <>
            <img
              className="h-10 w-37.5 dark:hidden"
              src={logo}
              alt="Logo"
            />
            <img
              className="hidden h-10 w-37.5 dark:block"
              src={logoDark}
              alt="Logo"
            />
          </>
        ) : (
          <img src={logoIcon} alt="Logo" className="size-8" />
        )}
      </Link>
    </SidebarHeader>
  );
}
