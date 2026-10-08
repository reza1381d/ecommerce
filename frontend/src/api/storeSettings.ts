import { apiClient } from "./client";

export type StorePalette =
  | "blue"
  | "emerald"
  | "violet"
  | "amber"
  | "rose"
  | "teal"
  | "cyan"
  | "indigo"
  | "fuchsia"
  | "lime"
  | "orange";

export type CurrencyUnit = "toman" | "rial";

export interface StoreSettingsResponse {
  store_name: string;
  palette: StorePalette;
  currency_unit: CurrencyUnit;
  home_hero_badge: string;
  home_hero_title: string;
  home_hero_description: string;
  home_hero_button_label: string;
  updated_at?: string;
}

export type StoreSettingsUpdate = Omit<StoreSettingsResponse, "updated_at">;

export function getStoreSettings() {
  return apiClient<StoreSettingsResponse>("/store/settings");
}

export function updateStoreSettings(
  token: string,
  settings: StoreSettingsUpdate,
) {
  return apiClient<StoreSettingsResponse>("/admin/store/settings", {
    method: "PUT",
    token,
    body: JSON.stringify(settings),
  });
}
