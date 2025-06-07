import en from "./en";
import { safeLocalStorage } from "@/app/utils";

// Type definitions for the locale system
export type LocaleType = typeof en;
export type PartialLocaleType = Partial<LocaleType>;

const localStorage = safeLocalStorage();

// English-only configuration for TDS Assistant
const ALL_LANGS = {
  en,
};

export type Lang = keyof typeof ALL_LANGS;

export const AllLangs = Object.keys(ALL_LANGS) as Lang[];

export const ALL_LANG_OPTIONS: Record<Lang, string> = {
  en: "English",
};

const LANG_KEY = "lang";
const DEFAULT_LANG = "en";

// Since we only support English, we can directly export the English locale
export default en as LocaleType;

function getItem(key: string) {
  return localStorage.getItem(key);
}

function setItem(key: string, value: string) {
  localStorage.setItem(key, value);
}

export function getLang(): Lang {
  // Always return English since it's the only supported language
  return "en";
}

export function changeLang(lang: Lang) {
  // Since we only support English, this function is simplified
  setItem(LANG_KEY, lang);
  location.reload();
}

export function getISOLang() {
  // Always return English ISO code
  return "en";
}

const DEFAULT_STT_LANG = "en-US";
export const STT_LANG_MAP: Record<Lang, string> = {
  en: "en-US",
};

export function getSTTLang(): string {
  return STT_LANG_MAP[getLang()] || DEFAULT_STT_LANG;
}
