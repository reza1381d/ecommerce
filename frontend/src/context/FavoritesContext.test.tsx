import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { FavoritesProvider, useFavorites } from "./FavoritesContext";

function FavoritesProbe() {
  const { favoriteIds, toggleFavorite } = useFavorites();
  return (
    <div>
      <output aria-label="شناسه‌های ذخیره‌شده">{favoriteIds.join(",")}</output>
      <button type="button" onClick={() => toggleFavorite(42)}>تغییر علاقه‌مندی</button>
    </div>
  );
}

function mountFavorites() {
  return render(<FavoritesProvider><FavoritesProbe /></FavoritesProvider>);
}

describe("favorites context", () => {
  beforeEach(() => localStorage.clear());
  afterEach(() => { cleanup(); localStorage.clear(); });

  it("toggles product IDs and persists the selection", () => {
    mountFavorites();
    fireEvent.click(screen.getByRole("button", { name: "تغییر علاقه‌مندی" }));

    expect(screen.getByLabelText("شناسه‌های ذخیره‌شده").textContent).toBe("42");
    expect(JSON.parse(localStorage.getItem("ecommerce_favorites_v1") ?? "[]")).toEqual([42]);

    fireEvent.click(screen.getByRole("button", { name: "تغییر علاقه‌مندی" }));
    expect(screen.getByLabelText("شناسه‌های ذخیره‌شده").textContent).toBe("");
  });

  it("restores valid IDs and ignores malformed stored data", () => {
    localStorage.setItem("ecommerce_favorites_v1", JSON.stringify([42, 42, -1, "9", 5.5]));
    const firstRender = mountFavorites();
    expect(screen.getByLabelText("شناسه‌های ذخیره‌شده").textContent).toBe("42");
    firstRender.unmount();

    localStorage.setItem("ecommerce_favorites_v1", "not-json");
    mountFavorites();
    expect(screen.getByLabelText("شناسه‌های ذخیره‌شده").textContent).toBe("");
  });
});
