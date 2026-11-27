import type React from "react";
export type MenuType = "main" | "support" | "others";
export interface SubItem {
  key: string;
  path: string;
  pro?: boolean;
  new?: boolean;
  target?: string;
  roles?: string[];
}
export interface NavItem {
  key: string;
  icon: React.ReactNode;
  path?: string;
  new?: boolean;
  target?: string;
  roles?: string[];
  subItems?: SubItem[];
}
