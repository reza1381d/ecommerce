import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

export type Calendar = "gregorian" | "jalali";
type DateFormatContextValue = { calendar: Calendar; setCalendar: (calendar: Calendar) => void; formatDate: (value: string | Date | null | undefined, options?: Intl.DateTimeFormatOptions) => string; formatPeriod: (value: string, groupBy: "day" | "month" | "year") => string; toCalendarDate: (isoDate: string | null | undefined) => string; fromCalendarDate: (date: string) => string | null; };
const DateFormatContext = createContext<DateFormatContextValue | null>(null);
const STORAGE_KEY = "ecommerce_calendar_preference";
const DAY_MS = 86_400_000;
const intlPersian = new Intl.DateTimeFormat("en-US-u-ca-persian-nu-latn", { timeZone: "UTC", year: "numeric", month: "numeric", day: "numeric" });
const intlGregorian = new Intl.DateTimeFormat("fa-IR-u-ca-gregory", { timeZone: "UTC" });

function numericParts(formatter: Intl.DateTimeFormat, date: Date) {
  const parts = Object.fromEntries(formatter.formatToParts(date).map(part => [part.type, part.value]));
  return { year: Number(parts.year), month: Number(parts.month), day: Number(parts.day) };
}
function digitsToLatin(value: string) {
  return value.replace(/[۰-۹٠-٩]/g, digit => String("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩".indexOf(digit) % 10));
}
function parseDateOnly(value: string) {
  const match = /^(\d{4})-(\d{1,2})-(\d{1,2})$/.exec(value);
  if (!match) return null;
  const [year, month, day] = match.slice(1).map(Number);
  const date = new Date(Date.UTC(year, month - 1, day));
  return date.getUTCFullYear() === year && date.getUTCMonth() === month - 1 && date.getUTCDate() === day ? { year, month, day } : null;
}
function gregorianToJalali(date: Date) { return numericParts(intlPersian, date); }
function jalaliToGregorian(year: number, month: number, day: number) {
  if (!Number.isInteger(year) || !Number.isInteger(month) || !Number.isInteger(day) || year < 1200 || year > 1600 || month < 1 || month > 12 || day < 1 || day > 31) return null;
  let low = Math.floor(Date.UTC(year + 621, 0, 1) / DAY_MS);
  let high = Math.floor(Date.UTC(year + 623, 0, 1) / DAY_MS);
  while (low < high) {
    const mid = Math.floor((low + high) / 2);
    const candidate = gregorianToJalali(new Date(mid * DAY_MS));
    const comparison = candidate.year - year || candidate.month - month || candidate.day - day;
    if (comparison < 0) low = mid + 1; else high = mid;
  }
  const result = new Date(low * DAY_MS);
  const check = gregorianToJalali(result);
  return check.year === year && check.month === month && check.day === day ? `${result.getUTCFullYear()}-${String(result.getUTCMonth() + 1).padStart(2, "0")}-${String(result.getUTCDate()).padStart(2, "0")}` : null;
}
function dateFromValue(value: string | Date) {
  if (value instanceof Date) return Number.isNaN(value.getTime()) ? null : value;
  const dateOnly = /^(\d{4}-\d{2}-\d{2})$/.exec(value);
  if (dateOnly) { const parsed = parseDateOnly(dateOnly[1]); return parsed ? new Date(Date.UTC(parsed.year, parsed.month - 1, parsed.day, 12)) : null; }
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date;
}
function dateInputValue(value: string | null | undefined, calendar: Calendar) {
  if (!value) return "";
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(value);
  if (!match) return "";
  if (calendar === "gregorian") return `${match[1]}-${match[2]}-${match[3]}`;
  const parsed = parseDateOnly(`${match[1]}-${match[2]}-${match[3]}`);
  if (!parsed) return "";
  const jalali = gregorianToJalali(new Date(Date.UTC(parsed.year, parsed.month - 1, parsed.day, 12)));
  return `${jalali.year}/${String(jalali.month).padStart(2, "0")}/${String(jalali.day).padStart(2, "0")}`;
}
function parseCalendarDate(value: string, calendar: Calendar) {
  const normalized = digitsToLatin(value.trim()).replace(/[./]/g, "-");
  if (calendar === "gregorian") {
    const parts = parseDateOnly(normalized);
    return parts ? `${String(parts.year).padStart(4, "0")}-${String(parts.month).padStart(2, "0")}-${String(parts.day).padStart(2, "0")}` : null;
  }
  const match = /^(\d{4})-(\d{1,2})-(\d{1,2})$/.exec(normalized);
  return match ? jalaliToGregorian(Number(match[1]), Number(match[2]), Number(match[3])) : null;
}
export function DateFormatProvider({ children }: { children: ReactNode }) {
  const [calendar, setCalendarState] = useState<Calendar>(() => { const saved = localStorage.getItem(STORAGE_KEY); return saved === "jalali" ? "jalali" : "gregorian"; });
  function setCalendar(next: Calendar) { setCalendarState(next); localStorage.setItem(STORAGE_KEY, next); }
  const value = useMemo<DateFormatContextValue>(() => ({
    calendar, setCalendar,
    formatDate(input, options = {}) {
      if (!input) return "—"; const date = dateFromValue(input); if (!date) return "—";
      const formatter = calendar === "jalali" ? new Intl.DateTimeFormat("fa-IR-u-ca-persian", { timeZone: "Asia/Tehran", dateStyle: "medium", ...options }) : new Intl.DateTimeFormat(intlGregorian.resolvedOptions().locale, { timeZone: "Asia/Tehran", dateStyle: "medium", ...options });
      return formatter.format(date);
    },
    formatPeriod(input, groupBy) {
      if (groupBy === "year") { const year = Number(input.slice(0, 4)); return calendar === "gregorian" ? year.toLocaleString("fa-IR") : String(gregorianToJalali(new Date(Date.UTC(year, 6, 1))).year).replace(/\d/g, digit => "۰۱۲۳۴۵۶۷۸۹"[Number(digit)]); }
      if (groupBy === "month") { const match = /^(\d{4})-(\d{1,2})/.exec(input); if (!match) return input; const date = dateFromValue(`${match[1]}-${match[2].padStart(2, "0")}-01`); if (!date) return input; const locale = calendar === "jalali" ? "fa-IR-u-ca-persian" : "fa-IR-u-ca-gregory"; return new Intl.DateTimeFormat(locale, { timeZone: "Asia/Tehran", month: "long", year: "numeric" }).format(date); }
      const date = dateFromValue(input);
      if (!date) return "—";
      const formatter = calendar === "jalali"
        ? new Intl.DateTimeFormat("fa-IR-u-ca-persian", { timeZone: "Asia/Tehran", dateStyle: "medium" })
        : new Intl.DateTimeFormat(intlGregorian.resolvedOptions().locale, { timeZone: "Asia/Tehran", dateStyle: "medium" });
      return formatter.format(date);
    },
    toCalendarDate(value) { return dateInputValue(value, calendar); },
    fromCalendarDate(value) { return parseCalendarDate(value, calendar); },
  }), [calendar]);
  return <DateFormatContext.Provider value={value}>{children}</DateFormatContext.Provider>;
}
export function useDateFormat() { const context = useContext(DateFormatContext); if (!context) throw new Error("useDateFormat must be used within DateFormatProvider"); return context; }
export function DateFormatSelector({ compact = false }: { compact?: boolean }) {
  const { calendar, setCalendar } = useDateFormat();
  return <label className={`inline-flex items-center gap-2 text-xs ${compact ? "text-slate-400" : "text-slate-300"}`}><span>تقویم</span><select aria-label="انتخاب تقویم" value={calendar} onChange={event => setCalendar(event.target.value as Calendar)} className="rounded-lg border border-slate-700 bg-slate-900 px-2 py-2 text-xs text-white"><option value="gregorian">میلادی</option><option value="jalali">شمسی</option></select></label>;
}
export function CalendarDateInput({ label, value, onChange }: { label: string; value?: string | null; onChange: (value: string | null) => void }) {
  const { calendar, toCalendarDate, fromCalendarDate } = useDateFormat();
  const shownValue = toCalendarDate(value);
  const [draft, setDraft] = useState(shownValue); const [error, setError] = useState("");
  const [calendarOpen, setCalendarOpen] = useState(false);
  const [viewYear, setViewYear] = useState(new Date().getFullYear());
  const [viewMonth, setViewMonth] = useState(new Date().getMonth() + 1);
  useEffect(() => { setDraft(shownValue); setError(""); }, [shownValue, calendar]);
  function update(raw: string) {
    setDraft(raw); setError(""); if (!raw) { onChange(null); return; }
    const date = fromCalendarDate(raw); if (!date) return;
    const oldTime = value && !Number.isNaN(new Date(value).getTime()) ? new Date(value).toISOString().slice(11, 19) : undefined;
    onChange(`${date}T${oldTime ?? (label.includes("پایان") ? "23:59:59" : "00:00:00")}Z`);
  }
  function updateFromPicker(raw: string) {
    const oldTime = value && !Number.isNaN(new Date(value).getTime()) ? new Date(value).toISOString().slice(11, 19) : undefined;
    const date = `${raw}T${oldTime ?? (label.includes("پایان") ? "23:59:59" : "00:00:00")}Z`;
    setDraft(toCalendarDate(date));
    setError("");
    onChange(date);
    setCalendarOpen(false);
  }
  function openPicker() {
    const stored = value && /^(\d{4})-(\d{2})-(\d{2})/.exec(value);
    const initialDate = stored
      ? new Date(Date.UTC(Number(stored[1]), Number(stored[2]) - 1, Number(stored[3]), 12))
      : new Date();
    const parts = calendar === "jalali"
      ? gregorianToJalali(initialDate)
      : { year: initialDate.getFullYear(), month: initialDate.getMonth() + 1, day: initialDate.getDate() };
    setViewYear(parts.year);
    setViewMonth(parts.month);
    setCalendarOpen(true);
  }

  function moveMonth(amount: number) {
    if (calendar === "gregorian") {
      const next = new Date(Date.UTC(viewYear, viewMonth - 1 + amount, 1, 12));
      setViewYear(next.getUTCFullYear());
      setViewMonth(next.getUTCMonth() + 1);
      return;
    }
    let nextMonth = viewMonth + amount;
    let nextYear = viewYear;
    if (nextMonth < 1) { nextMonth = 12; nextYear -= 1; }
    if (nextMonth > 12) { nextMonth = 1; nextYear += 1; }
    setViewYear(nextYear);
    setViewMonth(nextMonth);
  }

  const firstDate = calendar === "jalali"
    ? jalaliToGregorian(viewYear, viewMonth, 1)
    : `${String(viewYear).padStart(4, "0")}-${String(viewMonth).padStart(2, "0")}-01`;
  const firstDateObject = firstDate ? new Date(`${firstDate}T12:00:00Z`) : new Date();
  const monthLength = calendar === "jalali"
    ? (() => {
        const nextMonth = viewMonth === 12 ? jalaliToGregorian(viewYear + 1, 1, 1) : jalaliToGregorian(viewYear, viewMonth + 1, 1);
        return firstDate && nextMonth ? Math.round((Date.parse(`${nextMonth}T12:00:00Z`) - Date.parse(`${firstDate}T12:00:00Z`)) / DAY_MS) : 30;
      })()
    : new Date(Date.UTC(viewYear, viewMonth, 0)).getUTCDate();
  const weekdayOffset = calendar === "jalali"
    ? (firstDateObject.getUTCDay() + 1) % 7
    : firstDateObject.getUTCDay();
  const cellCount = Math.ceil((weekdayOffset + monthLength) / 7) * 7;
  const monthTitle = new Intl.DateTimeFormat(
    calendar === "jalali" ? "fa-IR-u-ca-persian" : "fa-IR-u-ca-gregory",
    { timeZone: "UTC", month: "long", year: "numeric" },
  ).format(firstDateObject);
  const weekDays = calendar === "jalali"
    ? ["ش", "ی", "د", "س", "چ", "پ", "ج"]
    : ["ی", "د", "س", "چ", "پ", "ج", "ش"];
  const selectedDate = value && /^(\d{4})-(\d{2})-(\d{2})/.exec(value);
  const selectedIso = selectedDate ? `${selectedDate[1]}-${selectedDate[2]}-${selectedDate[3]}` : "";

  return (
    <div className="block text-sm text-slate-400">
      <label>{label}</label>
      <div className="relative mt-2">
        <input
          type="text"
          inputMode={calendar === "jalali" ? "numeric" : undefined}
          placeholder={calendar === "jalali" ? "۱۴۰۵/۰۱/۰۱" : "YYYY-MM-DD"}
          value={draft}
          onChange={event => update(event.target.value)}
          onBlur={() => { if (draft && !fromCalendarDate(draft)) setError("تاریخ معتبر وارد کنید."); }}
          className="block w-full rounded-xl border border-slate-700 bg-slate-950 py-3 pl-12 pr-4 text-white"
        />
        <button
          type="button"
          onClick={openPicker}
          aria-label={`بازکردن تقویم برای ${label}`}
          aria-expanded={calendarOpen}
          aria-haspopup="dialog"
          title="انتخاب از تقویم"
          className="absolute left-2 top-1/2 z-10 -translate-y-1/2 rounded-lg p-2 text-slate-400 transition hover:bg-slate-800 hover:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" className="h-5 w-5" stroke="currentColor" strokeWidth="1.8">
            <rect x="3.5" y="5" width="17" height="16" rx="2" />
            <path d="M7.5 3v4M16.5 3v4M3.5 9.5h17M8 13h.01M12 13h.01M16 13h.01M8 17h.01M12 17h.01" strokeLinecap="round" />
          </svg>
        </button>
        {calendarOpen && (
          <div role="dialog" aria-label={`انتخاب ${label}`} className="absolute left-0 top-full z-50 mt-2 w-80 max-w-[calc(100vw-2rem)] rounded-2xl border border-slate-700 bg-slate-900 p-4 shadow-2xl shadow-black/50">
            <div className="mb-4 flex items-center justify-between">
              <button type="button" onClick={() => moveMonth(-1)} aria-label="ماه قبل" className="rounded-lg px-3 py-2 text-lg text-slate-300 hover:bg-slate-800">‹</button>
              <p className="font-semibold text-white">{monthTitle}</p>
              <button type="button" onClick={() => moveMonth(1)} aria-label="ماه بعد" className="rounded-lg px-3 py-2 text-lg text-slate-300 hover:bg-slate-800">›</button>
            </div>
            <div className="grid grid-cols-7 gap-1 text-center text-xs text-slate-500">
              {weekDays.map((day, index) => <span key={`${day}-${index}`} className="py-2">{day}</span>)}
              {Array.from({ length: cellCount }, (_, index) => {
                const day = index - weekdayOffset + 1;
                if (day < 1 || day > monthLength || !firstDate) return <span key={`empty-${index}`} />;
                const isoDate = calendar === "jalali"
                  ? jalaliToGregorian(viewYear, viewMonth, day)
                  : `${String(viewYear).padStart(4, "0")}-${String(viewMonth).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
                if (!isoDate) return <span key={`invalid-${index}`} />;
                const isSelected = isoDate === selectedIso;
                return (
                  <button
                    key={isoDate}
                    type="button"
                    onClick={() => updateFromPicker(isoDate)}
                    aria-pressed={isSelected}
                    className={`rounded-lg py-2 transition ${isSelected ? "bg-blue-600 font-bold text-white" : "text-slate-200 hover:bg-slate-700"}`}
                  >
                    {day.toLocaleString("fa-IR")}
                  </button>
                );
              })}
            </div>
            <div className="mt-3 flex justify-end border-t border-slate-800 pt-3">
              <button type="button" onClick={() => setCalendarOpen(false)} className="rounded-lg px-3 py-2 text-xs text-slate-400 hover:bg-slate-800 hover:text-white">بستن</button>
            </div>
          </div>
        )}
      </div>
      {error && <span role="alert" className="mt-1 block text-xs text-red-300">{error}</span>}
    </div>
  );
}
