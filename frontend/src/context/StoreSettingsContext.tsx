import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import {
  getStoreSettings,
  updateStoreSettings,
  type StorePalette,
  type StoreSettingsResponse,
} from "../api/storeSettings";
import { useAuth } from "./AuthContext";
import type { CurrencyUnit } from "../utils/currency";

export interface StoreSettings {
  storeName: string;
  palette: StorePalette;
  currencyUnit: CurrencyUnit;
  homeHeroBadge: string;
  homeHeroTitle: string;
  homeHeroDescription: string;
  homeHeroButtonLabel: string;
}

interface StoreSettingsContextValue {
  settings: StoreSettings;
  loading: boolean;
  saveSettings: (settings: StoreSettings) => Promise<void>;
}

const DEFAULT_SETTINGS: StoreSettings = {
  storeName: "فروشگاه اینترنتی",
  palette: "blue",
  currencyUnit: "toman",
  homeHeroBadge: "فروشگاه اینترنتی",
  homeHeroTitle: "خریدی ساده،\nانتخابی مطمئن",
  homeHeroDescription:
    "محصولات فروشگاه را ببینید، جست‌وجو کنید و گزینه‌ی مناسب خودتان را پیدا کنید.",
  homeHeroButtonLabel: "مشاهده محصولات",
};

const PALETTES: StorePalette[] = [
  "blue", "emerald", "violet", "amber", "rose", "teal",
  "cyan", "indigo", "fuchsia", "lime", "orange",
];
const StoreSettingsContext = createContext<StoreSettingsContextValue | null>(null);

function toStoreSettings(value: StoreSettingsResponse): StoreSettings {
  return {
    storeName: value.store_name,
    palette: value.palette,
    currencyUnit: value.currency_unit ?? "toman",
    homeHeroBadge: value.home_hero_badge,
    homeHeroTitle: value.home_hero_title,
    homeHeroDescription: value.home_hero_description,
    homeHeroButtonLabel: value.home_hero_button_label,
  };
}

export function StoreSettingsProvider({ children }: { children: ReactNode }) {
  const { token } = useAuth();
  const [settings, setSettings] = useState(DEFAULT_SETTINGS);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    let firstLoad = true;
    async function refreshSettings() {
      try {
        const result = await getStoreSettings();
        if (active && PALETTES.includes(result.palette) && result.store_name.trim()) {
          setSettings(toStoreSettings(result));
        }
      } catch {
        // Keep the last known values if settings cannot be refreshed.
      } finally {
        if (active && firstLoad) setLoading(false);
        firstLoad = false;
      }
    }
    function refreshWhenVisible() { if (document.visibilityState === "visible") void refreshSettings(); }
    void refreshSettings();
    const timer = window.setInterval(() => void refreshSettings(), 60_000);
    window.addEventListener("focus", refreshWhenVisible);
    document.addEventListener("visibilitychange", refreshWhenVisible);
    return () => {
      active = false;
      window.clearInterval(timer);
      window.removeEventListener("focus", refreshWhenVisible);
      document.removeEventListener("visibilitychange", refreshWhenVisible);
    };
  }, []);

  useEffect(() => {
    document.documentElement.dataset.storePalette = settings.palette;
    document.documentElement.dataset.currencyUnit = settings.currencyUnit;
    document.title = settings.storeName;
  }, [settings]);

  const saveSettings = useCallback(async (next: StoreSettings) => {
    if (!token) throw new Error("برای ذخیره تنظیمات باید با حساب مدیر وارد شده باشی.");

    const payload = {
      store_name: next.storeName.trim(),
      palette: next.palette,
      currency_unit: next.currencyUnit,
      home_hero_badge: next.homeHeroBadge.trim(),
      home_hero_title: next.homeHeroTitle.trim(),
      home_hero_description: next.homeHeroDescription.trim(),
      home_hero_button_label: next.homeHeroButtonLabel.trim(),
    };
    if (Object.values(payload).some((value) => typeof value === "string" && !value)) {
      throw new Error("فیلدهای تنظیمات نمی‌توانند خالی باشند.");
    }

    const saved = await updateStoreSettings(token, payload);
    setSettings(toStoreSettings(saved));
  }, [token]);

  const value = useMemo(
    () => ({ settings, loading, saveSettings }),
    [settings, loading, saveSettings],
  );
  return (
    <StoreSettingsContext.Provider value={value}>
      {children}
    </StoreSettingsContext.Provider>
  );
}

export function useStoreSettings() {
  const value = useContext(StoreSettingsContext);
  if (!value) throw new Error("useStoreSettings must be used inside StoreSettingsProvider");
  return value;
}
