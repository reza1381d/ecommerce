import { useEffect, useState, type FormEvent } from "react";
import { useStoreSettings, type StoreSettings } from "../context/StoreSettingsContext";
import type { StorePalette } from "../api/storeSettings";

const OPTIONS: { id: StorePalette; label: string; color: string; description: string }[] = [
  { id: "blue", label: "آبی", color: "#2563eb", description: "آبی کلاسیک" },
  { id: "emerald", label: "سبز زمردی", color: "#059669", description: "سبز آرام" },
  { id: "violet", label: "بنفش", color: "#7c3aed", description: "بنفش مدرن" },
  { id: "amber", label: "کهربایی", color: "#d97706", description: "گرم و پرانرژی" },
  { id: "rose", label: "رز", color: "#e11d48", description: "صورتی متمایل به قرمز" },
  { id: "teal", label: "سبزآبی", color: "#0d9488", description: "سبزآبی متعادل" },
  { id: "cyan", label: "فیروزه‌ای", color: "#0891b2", description: "فیروزه‌ای روشن" },
  { id: "indigo", label: "نیلی", color: "#4f46e5", description: "آبی نیلی" },
  { id: "fuchsia", label: "فوشیا", color: "#c026d3", description: "بنفش صورتی" },
  { id: "lime", label: "لیمویی", color: "#65a30d", description: "سبز لیمویی" },
  { id: "orange", label: "نارنجی", color: "#ea580c", description: "نارنجی پرانرژی" },
];

export default function AdminSettingsPage() {
  const { settings, loading, saveSettings } = useStoreSettings();
  const [form, setForm] = useState<StoreSettings>(settings);
  const [saving, setSaving] = useState(false);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  useEffect(() => setForm(settings), [settings]);

  function update<K extends keyof StoreSettings>(key: K, value: StoreSettings[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setNotice("");
    setSaving(true);
    try {
      await saveSettings(form);
      setNotice("تنظیمات در سرور ذخیره شد و برای بازدیدکنندگان فروشگاه اعمال می‌شود.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "ذخیره تنظیمات انجام نشد.");
    } finally {
      setSaving(false);
    }
  }

  const selectedColor = OPTIONS.find((option) => option.id === form.palette)?.color ?? "#2563eb";

  return (
    <section dir="rtl" className="mx-auto max-w-4xl space-y-7">
      <header>
        <h1 className="text-3xl font-black text-white">تنظیمات فروشگاه</h1>
        <p className="mt-2 text-slate-400">نام فروشگاه، بنر صفحه‌ی خانه و پالت رنگی مشترک را تنظیم کن.</p>
      </header>

      {loading ? (
        <div aria-live="polite" className="rounded-2xl border border-slate-800 bg-slate-900 p-8 text-slate-400">
          در حال دریافت تنظیمات ذخیره‌شده...
        </div>
      ) : (
        <form onSubmit={submit} className="space-y-7 rounded-3xl border border-slate-800 bg-slate-900/80 p-6 backdrop-blur-xl sm:p-8">
          <label className="block text-sm font-medium text-slate-300">
            نام فروشگاه / عنوان تب مرورگر
            <input
              required
              maxLength={60}
              value={form.storeName}
              onChange={(event) => update("storeName", event.target.value)}
              className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none focus:border-blue-500"
              placeholder="مثلاً فروشگاه من"
            />
            <span className="mt-2 block text-xs text-slate-500">در عنوان تب، سربرگ و پایین صفحه نمایش داده می‌شود.</span>
          </label>

          <label className="block text-sm font-medium text-slate-300">
            واحد پول فروشگاه
            <select value={form.currencyUnit} onChange={event => update("currencyUnit", event.target.value as StoreSettings["currencyUnit"])} className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white">
              <option value="toman">تومان</option><option value="rial">ریال</option>
            </select>
            <span className="mt-2 block text-xs text-slate-500">مبالغ برای همهٔ کاربران تبدیل می‌شوند؛ مقدار اصلی به‌صورت عدد صحیح تومان ذخیره می‌شود.</span>
          </label>

          <fieldset className="space-y-4 rounded-2xl border border-slate-800 p-5">
            <legend className="px-2 text-lg font-bold text-white">متن بنر صفحه‌ی خانه</legend>
            <label className="block text-sm font-medium text-slate-300">
              برچسب بالای تیتر
              <input
                required maxLength={80} value={form.homeHeroBadge}
                onChange={(event) => update("homeHeroBadge", event.target.value)}
                className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none focus:border-blue-500"
                placeholder="مثلاً E-Commerce"
              />
            </label>
            <label className="block text-sm font-medium text-slate-300">
              تیتر اصلی
              <textarea
                required maxLength={160} rows={2} value={form.homeHeroTitle}
                onChange={(event) => update("homeHeroTitle", event.target.value)}
                className="mt-2 w-full resize-y rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none focus:border-blue-500"
                placeholder="مثلاً خریدی ساده، انتخابی مطمئن"
              />
              <span className="mt-1 block text-xs text-slate-500">برای شکستن تیتر به چند خط، Enter بزن.</span>
            </label>
            <label className="block text-sm font-medium text-slate-300">
              توضیح زیر تیتر
              <textarea
                required maxLength={500} rows={3} value={form.homeHeroDescription}
                onChange={(event) => update("homeHeroDescription", event.target.value)}
                className="mt-2 w-full resize-y rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none focus:border-blue-500"
                placeholder="توضیح کوتاه فروشگاه برای بازدیدکنندگان"
              />
            </label>
            <label className="block text-sm font-medium text-slate-300">
              متن دکمه
              <input
                required maxLength={50} value={form.homeHeroButtonLabel}
                onChange={(event) => update("homeHeroButtonLabel", event.target.value)}
                className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none focus:border-blue-500"
                placeholder="مثلاً مشاهده محصولات"
              />
              <span className="mt-1 block text-xs text-slate-500">دکمه همچنان به صفحه‌ی محصولات می‌رود.</span>
            </label>
          </fieldset>

          <fieldset>
            <legend className="text-sm font-medium text-slate-300">پالت رنگی مشترک</legend>
            <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {OPTIONS.map((option) => (
                <label
                  key={option.id}
                  className={`flex cursor-pointer items-center gap-3 rounded-2xl border p-4 transition ${form.palette === option.id ? "border-white/30 bg-white/[0.08]" : "border-slate-800 bg-slate-950/50 hover:border-slate-700"}`}
                >
                  <input
                    type="radio" name="palette" value={option.id}
                    checked={form.palette === option.id}
                    onChange={() => update("palette", option.id)} className="sr-only"
                  />
                  <span aria-hidden="true" className="h-10 w-10 rounded-xl shadow-lg" style={{ backgroundColor: option.color }} />
                  <span>
                    <span className="block font-medium text-white">{option.label}</span>
                    <span className="mt-1 block text-xs text-slate-500">{option.description}</span>
                  </span>
                  {form.palette === option.id && <span className="mr-auto text-xs text-emerald-300">انتخاب‌شده</span>}
                </label>
              ))}
            </div>
          </fieldset>

          <div>
            <p className="mb-3 text-sm font-medium text-slate-300">پیش‌نمایش بنر</p>
            <section className="store-hero rounded-3xl border p-6 sm:p-8">
              <p className="text-sm font-semibold" style={{ color: selectedColor }}>{form.homeHeroBadge || "برچسب فروشگاه"}</p>
              <h2 className="mt-3 whitespace-pre-line text-2xl font-black leading-tight text-white sm:text-3xl">
                {form.homeHeroTitle || "تیتر اصلی"}
              </h2>
              <p className="mt-3 whitespace-pre-line leading-7 text-slate-300">
                {form.homeHeroDescription || "توضیح کوتاه فروشگاه"}
              </p>
              <span className="mt-5 inline-flex rounded-xl px-5 py-2.5 font-medium text-white" style={{ backgroundColor: selectedColor }}>
                {form.homeHeroButtonLabel || "متن دکمه"}
              </span>
            </section>
          </div>

          {error && <p role="alert" className="text-sm text-red-300">{error}</p>}
          {notice && <p role="status" className="text-sm text-emerald-300">{notice}</p>}
          <button type="submit" disabled={saving} className="rounded-xl bg-blue-600 px-6 py-3 font-semibold text-white transition hover:bg-blue-500 disabled:opacity-50">
            {saving ? "در حال ذخیره..." : "ذخیره برای همه کاربران"}
          </button>
        </form>
      )}
    </section>
  );
}
