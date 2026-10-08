import { describe, expect, it } from "vitest";
import { currencyInputValue, currencyStorageValue, formatMoney } from "./currency";

describe("currency utilities", () => {
  it("formats whole toman values without decimal fractions", () => {
    expect(formatMoney("125.7", "toman")).toBe("۱۲۶ تومان");
  });

  it("converts the stored toman amount to rial for display", () => {
    expect(currencyInputValue(12, "rial")).toBe(120);
    expect(formatMoney(12, "rial")).toBe("۱۲۰ ریال");
  });

  it("stores only whole toman amounts and rejects unrepresentable rial inputs", () => {
    expect(currencyStorageValue(125, "toman")).toBe(125);
    expect(currencyStorageValue(120, "rial")).toBe(12);
    expect(currencyStorageValue(125, "rial")).toBeNull();
  });
});
