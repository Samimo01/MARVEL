import { LayoutGridIcon, UserCircleIcon } from "@/icons";
import type { NavItem } from "./types";

export const navItems: NavItem[] = [
  {
    icon: <LayoutGridIcon className="size-6" />,
    key: "dashboard",
    subItems: [{ key: "dashboard", path: "/" }],
  },
  {
    icon: <UserCircleIcon className="size-6" />,
    key: "userProfile",
    path: "/profile",
  },
];

export const othersItems: NavItem[] = [];
export const supportItems: NavItem[] = [];
