import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { DateFormatProvider, useDateFormat } from "./DateFormatContext";

function CalendarProbe() {
  const { calendar, setCalendar, toCalendarDate, fromCalendarDate } = useDateFormat();
  return (
    <div>
      <output aria-label="تقویم فعال">{calendar}</output>
      <output aria-label="تاریخ شمسی">{toCalendarDate("2026-10-08")}</output>
      <output aria-label="تاریخ میلادی">{fromCalendarDate("1405/07/16")}</output>
      <button type="button" onClick={() => setCalendar("jalali")}>شمسی</button>
    </div>
  );
}

describe("date format context", () => {
  beforeEach(() => localStorage.clear());
  afterEach(() => { cleanup(); localStorage.clear(); });

  it("converts Jalali dates to the stored Gregorian date and saves the preference", () => {
    render(<DateFormatProvider><CalendarProbe /></DateFormatProvider>);
    fireEvent.click(screen.getByRole("button", { name: "شمسی" }));

    expect(screen.getByLabelText("تقویم فعال").textContent).toBe("jalali");
    expect(screen.getByLabelText("تاریخ شمسی").textContent).toBe("1405/07/16");
    expect(screen.getByLabelText("تاریخ میلادی").textContent).toBe("2026-10-08");
    expect(localStorage.getItem("ecommerce_calendar_preference")).toBe("jalali");
  });

  it("rejects invalid Jalali dates", () => {
    function InvalidDateProbe() {
      const { fromCalendarDate } = useDateFormat();
      return <output aria-label="تاریخ نامعتبر">{String(fromCalendarDate("1405/13/01"))}</output>;
    }
    render(<DateFormatProvider><InvalidDateProbe /></DateFormatProvider>);
    expect(screen.getByLabelText("تاریخ نامعتبر").textContent).toBe("null");
  });
});
