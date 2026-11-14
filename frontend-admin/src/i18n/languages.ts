import type { ComponentType, SVGProps } from "react";

import ArFlagIcon from "@/icons/flag-sa.svg?react";
import FrFlagIcon from "@/icons/flag-fr.svg?react";
import UsFlagIcon from "@/icons/flag-us.svg?react";

import { type Locale, isRtl, routing } from "./routing";

export interface Language {
  id: Locale;
  /** Native display name. */
  name: string;
  /** Short code shown in compact UI (e.g. the dropdown trigger). */
  shortName: string;
  FlagIcon: ComponentType<SVGProps<SVGSVGElement>>;
  badge?: string;
}

export const languages: readonly Language[] = [
  { id: "en", name: "English", shortName: "EN", FlagIcon: UsFlagIcon },
  { id: "fr", name: "Français", shortName: "FR", FlagIcon: FrFlagIcon },
  { id: "ar", name: "العربية", shortName: "AR", FlagIcon: ArFlagIcon },
];

const defaultLanguage = languages.find(
  (language) => language.id === routing.defaultLocale,
) as Language;

export const getLanguage = (locale: Locale): Language =>
  languages.find((language) => language.id === locale) ?? defaultLanguage;

export { isRtl };
