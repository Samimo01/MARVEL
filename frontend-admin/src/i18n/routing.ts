export const routing = {
  locales: ["en", "fr", "ar"] as const,
  defaultLocale: "en",
} as const;

export type Locale = (typeof routing.locales)[number];

export const isLocale = (v: unknown): v is Locale =>
  routing.locales.includes(v as Locale);

const RTL_LOCALES: readonly Locale[] = ["ar"];

export const isRtl = (locale: Locale): boolean => RTL_LOCALES.includes(locale);
