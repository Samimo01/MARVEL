import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  useSidebar,
} from "@/components/ui/sidebar";
import { useState } from "react";
import { useLocation } from "react-router";
import { navItems, othersItems, supportItems } from "./data";
import AppSidebarHeader from "./sidebar-header";
import SidebarNavGroup from "./sidebar-nav-group";
import SidebarWidget from "./sidebar-widget";
import type { MenuType, NavItem } from "./types";
import { useSession } from "@/app/auth/session-context";
import { hasAnyRole } from "@/app/auth/permissions";
export default function AppSidebar() {
  const { open, isMobile, isHovered } = useSidebar();
  const { pathname } = useLocation();
  const { roles } = useSession();
  const showContent = open || isHovered || isMobile;
  const filtered = (items: NavItem[]) =>
    items
      .map((item) => ({
        ...item,
        subItems: item.subItems?.filter(
          (sub) => !sub.roles || hasAnyRole(roles, sub.roles),
        ),
      }))
      .filter(
        (item) =>
          (!item.roles || hasAnyRole(roles, item.roles)) &&
          (item.subItems ? item.subItems.length > 0 : true),
      );
  const sections: { type: MenuType; labelKey: string; items: NavItem[] }[] = [
    { type: "main", labelKey: "groups.menu", items: filtered(navItems) },
    {
      type: "support",
      labelKey: "groups.support",
      items: filtered(supportItems),
    },
    { type: "others", labelKey: "groups.others", items: filtered(othersItems) },
  ];
  const findMatchingSubmenu = (path: string) => {
    for (const section of sections)
      for (let index = 0; index < section.items.length; index++) {
        if (
          section.items[index].subItems?.some(
            (item) =>
              item.path === path ||
              (path.startsWith(`${item.path}/`) && item.path !== "/"),
          )
        )
          return { type: section.type, index };
      }
    return null;
  };
  const [openSubmenu, setOpenSubmenu] = useState<{
    type: MenuType;
    index: number;
  } | null>(() => findMatchingSubmenu(pathname));
  const [prevPath, setPrevPath] = useState(pathname);
  if (prevPath !== pathname) {
    setPrevPath(pathname);
    setOpenSubmenu(findMatchingSubmenu(pathname));
  }
  const toggle = (index: number, type: MenuType) =>
    setOpenSubmenu((current) =>
      current?.type === type && current.index === index
        ? null
        : { type, index },
    );
  return (
    <Sidebar side="left" collapsible="icon">
      <AppSidebarHeader showContent={showContent} />
      <SidebarContent className="overflow-y-auto px-5 duration-300 ease-linear">
        <nav className="mb-6">
          <div className="flex flex-col gap-4">
            {sections
              .filter((section) => section.items.length > 0)
              .map((section) => (
                <SidebarNavGroup
                  key={section.type}
                  labelKey={section.labelKey}
                  menuType={section.type}
                  items={section.items}
                  openSubmenu={openSubmenu}
                  showContent={showContent}
                  pathname={pathname}
                  onToggleSubmenu={toggle}
                />
              ))}
          </div>
        </nav>
      </SidebarContent>
      {showContent && (
        <SidebarFooter className="p-0 px-5 pt-1 pb-4">
          <SidebarWidget />
        </SidebarFooter>
      )}
    </Sidebar>
  );
}
