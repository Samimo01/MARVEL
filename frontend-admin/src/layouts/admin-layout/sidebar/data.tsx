import {
  LayoutGridIcon,
  UserCircleIcon,
  FolderIcon,
  BoxIcon,
  DollarIcon,
  UsersIcon,
} from "@/icons";
import type { NavItem } from "./types";
import { PAGE_PERMISSIONS } from "@/app/auth/permissions";
export const navItems: NavItem[] = [
  {
    icon: <LayoutGridIcon className="size-6" />,
    key: "dashboard",
    subItems: [
      { key: "dashboard", path: "/", roles: PAGE_PERMISSIONS.dashboard },
    ],
  },
  {
    icon: <FolderIcon className="size-6" />,
    key: "collection",
    subItems: [
      {
        key: "campaigns",
        path: "/campaigns",
        roles: PAGE_PERMISSIONS.campaigns,
      },
      {
        key: "financialDonations",
        path: "/financial-donations",
        roles: PAGE_PERMISSIONS.financialDonations,
      },
      {
        key: "naturalDonations",
        path: "/natural-donations",
        roles: PAGE_PERMISSIONS.naturalDonations,
      },
      { key: "collects", path: "/collects", roles: PAGE_PERMISSIONS.collects },
      { key: "missions", path: "/missions", roles: PAGE_PERMISSIONS.missions },
    ],
  },
  {
    icon: <BoxIcon className="size-6" />,
    key: "resources",
    subItems: [
      { key: "stock", path: "/stock", roles: PAGE_PERMISSIONS.stock },
      {
        key: "beneficiaries",
        path: "/beneficiaries",
        roles: PAGE_PERMISSIONS.beneficiaries,
      },
      {
        key: "distributions",
        path: "/distributions",
        roles: PAGE_PERMISSIONS.distributions,
      },
    ],
  },
  {
    icon: <DollarIcon className="size-6" />,
    key: "finance",
    subItems: [
      { key: "treasury", path: "/treasury", roles: PAGE_PERMISSIONS.treasury },
      { key: "receipts", path: "/receipts", roles: PAGE_PERMISSIONS.receipts },
    ],
  },
  {
    icon: <UsersIcon className="size-6" />,
    key: "administration",
    subItems: [{ key: "users", path: "/users", roles: PAGE_PERMISSIONS.users }],
  },
  {
    icon: <UserCircleIcon className="size-6" />,
    key: "account",
    path: "/profile",
    roles: PAGE_PERMISSIONS.profile,
  },
];
export const othersItems: NavItem[] = [];
export const supportItems: NavItem[] = [];
