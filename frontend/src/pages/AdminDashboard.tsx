import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { getCategories } from "../api/categories";
import { getProducts, type Product } from "../api/products";
import {
  getDashboardStats,
  getProductSales,
  getSalesTimeline,
  type AnalyticsPeriod,
  type DashboardStats,
  type ProductSalesItem,
  type SalesGroupBy,
  type SalesTimelineItem,
} from "../api/adminAccounting";
import { useAuth } from "../context/AuthContext";
import { CalendarDateInput, useDateFormat } from "../context/DateFormatContext";
import { formatMoney as money } from "../utils/currency";

type Tab = "chart" | "products" | "periods";
const TABS: { id: Tab; label: string }[] = [
  { id: "chart", label: "نمودار فروش" },
  { id: "products", label: "تعداد فروش هر محصول" },
  { id: "periods", label: "فروش روزانه، ماهانه و سالانه" },
];
const PERIODS: { id: AnalyticsPeriod; label: string }[] = [
  { id: "7d", label: "۷ روز" },
  { id: "30d", label: "۳۰ روز" },
  { id: "90d", label: "۹۰ روز" },
];
const GROUPS: { id: SalesGroupBy; label: string }[] = [
  { id: "day", label: "روزانه" },
  { id: "month", label: "ماهانه" },
  { id: "year", label: "سالانه" },
];

function dateDaysAgo(days: number) {
  const date = new Date();
  date.setDate(date.getDate() - days);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
}

function savedLowStockThreshold() {
  try {
    const storedValue = localStorage.getItem("ecommerce_low_stock_threshold");
    if (storedValue === null) return 5;
    const saved = Number(storedValue);
    return Number.isInteger(saved) && saved >= 0 ? saved : 5;
  } catch {
    return 5;
  }
}

function matchesDateRange(period: string, groupBy: SalesGroupBy, from: string, to: string) {
  if (groupBy === "day") return period >= from && period <= to;
  if (groupBy === "month") return period >= from.slice(0, 7) && period <= to.slice(0, 7);
  return period >= from.slice(0, 4) && period <= to.slice(0, 4);
}

function downloadSalesCsv(items: SalesTimelineItem[], groupBy: SalesGroupBy, from: string, to: string) {
  const escapeCell = (value: string | number) => `"${String(value).replaceAll('"', '""')}"`;
  const rows: (string | number)[][] = [
    ["بازه", "تعداد سفارش", "تعداد کالای فروخته‌شده", "فروش"],
    ...items.map((item) => [item.period, item.orders, item.units_sold, item.revenue]),
  ];
  const csv = `\uFEFF${rows.map((row) => row.map(escapeCell).join(",")).join("\r\n")}`;
  const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = `sales-${groupBy}-${from}-${to}.csv`;
  link.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export default function AdminDashboard() {
  const { token } = useAuth();
  const { formatDate, formatPeriod } = useDateFormat();
  const [summary, setSummary] = useState({ products: 0, activeProducts: 0, categories: 0 });
  const [summaryLoading, setSummaryLoading] = useState(true);
  const [summaryError, setSummaryError] = useState("");
  const [summaryRetry, setSummaryRetry] = useState(0);
  const [inventoryProducts, setInventoryProducts] = useState<Product[]>([]);
  const [lowStockThreshold, setLowStockThreshold] = useState(savedLowStockThreshold);
  const [tab, setTab] = useState<Tab>("chart");
  const [period, setPeriod] = useState<AnalyticsPeriod>("30d");
  const [groupBy, setGroupBy] = useState<SalesGroupBy>("day");
  const [reportFrom, setReportFrom] = useState(() => dateDaysAgo(29));
  const [reportTo, setReportTo] = useState(() => dateDaysAgo(0));
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [products, setProducts] = useState<ProductSalesItem[]>([]);
  const [timeline, setTimeline] = useState<SalesTimelineItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  const rangeIsOrdered = Boolean(reportFrom && reportTo && reportFrom <= reportTo);
  const rangeBucketCount = !rangeIsOrdered ? 0 : groupBy === "day"
    ? Math.round((Date.parse(`${reportTo}T00:00:00Z`) - Date.parse(`${reportFrom}T00:00:00Z`)) / 86_400_000) + 1
    : groupBy === "month"
      ? (Number(reportTo.slice(0, 4)) - Number(reportFrom.slice(0, 4))) * 12
        + Number(reportTo.slice(5, 7)) - Number(reportFrom.slice(5, 7)) + 1
      : Number(reportTo.slice(0, 4)) - Number(reportFrom.slice(0, 4)) + 1;
  const rangeTooLarge = rangeBucketCount > 366;
  const rangeIsValid = rangeIsOrdered && !rangeTooLarge;

  useEffect(() => {
    let active = true;
    async function load() {
      setSummaryLoading(true);
      setSummaryError("");
      try {
        const [all, activeProducts, categories] = await Promise.all([
          getProducts({ page: 1, limit: 1 }),
          getProducts({ page: 1, limit: 100, isActive: true }),
          getCategories(),
        ]);
        const pageCount = Math.ceil(activeProducts.total / activeProducts.limit);
        const remainingPages = await Promise.all(
          Array.from({ length: Math.max(0, pageCount - 1) }, (_, index) =>
            getProducts({ page: index + 2, limit: activeProducts.limit, isActive: true }),
          ),
        );
        if (active) {
          setSummary({ products: all.total, activeProducts: activeProducts.total, categories: categories.filter((item) => item.is_active).length });
          setInventoryProducts([...activeProducts.items, ...remainingPages.flatMap((page) => page.items)]);
        }
      } catch (err) {
        if (active) setSummaryError(err instanceof Error ? err.message : "دریافت خلاصه داشبورد انجام نشد.");
      } finally {
        if (active) setSummaryLoading(false);
      }
    }
    void load();
    return () => { active = false; };
  }, [summaryRetry]);

  useEffect(() => {
    let active = true;
    async function loadAnalytics() {
      if (!token) return;
      setLoading(true);
      setError("");
      try {
        if (tab === "chart") {
          const result = await getDashboardStats(token, period);
          if (active) setStats(result);
        } else if (tab === "products") {
          const result = await getProductSales(token, period, 10);
          if (active) setProducts(result.items);
        } else if (rangeIsValid) {
          const result = await getSalesTimeline(token, groupBy, 366, reportFrom, reportTo);
          if (active) setTimeline(result.items);
        } else {
          if (active) setTimeline([]);
        }
      } catch (err) {
        if (active) setError(err instanceof Error ? err.message : "دریافت آمار فروش ناموفق بود.");
      } finally {
        if (active) setLoading(false);
      }
    }
    void loadAnalytics();
    return () => { active = false; };
  }, [token, tab, period, groupBy, reportFrom, reportTo, rangeIsValid, retry]);

  const cards = [
    { label: "همه محصولات", value: summary.products },
    { label: "محصولات فعال", value: summary.activeProducts },
    { label: "دسته‌بندی‌های فعال", value: summary.categories },
  ];
  const lowStockProducts = useMemo(
    () => inventoryProducts.filter((product) => product.available_stock <= lowStockThreshold)
      .sort((a, b) => a.available_stock - b.available_stock),
    [inventoryProducts, lowStockThreshold],
  );
  const filteredTimeline = useMemo(
    () => rangeIsValid ? timeline.filter((item) => matchesDateRange(item.period, groupBy, reportFrom, reportTo)) : [],
    [timeline, groupBy, reportFrom, reportTo, rangeIsValid],
  );

  return (
    <div dir="rtl" className="space-y-8">
      <header>
        <h1 className="text-3xl font-black text-white">داشبورد</h1>
        <p className="mt-2 text-slate-400">نمای کلی فروشگاه و گزارش‌های فروش</p>
      </header>

      {summaryError && <div role="alert" className="rounded-2xl border border-red-900/50 bg-red-950/30 p-4 text-red-300">{summaryError}<button type="button" onClick={() => setSummaryRetry((value) => value + 1)} className="mr-3 underline">تلاش دوباره</button></div>}

      <section aria-label="آمار محصولات" aria-busy={summaryLoading} className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {cards.map((card) => <article key={card.label} className="rounded-2xl border border-slate-800 bg-slate-900 p-6"><p className="text-sm text-slate-400">{card.label}</p><p className="mt-3 text-2xl font-bold text-white">{summaryLoading ? "..." : card.value.toLocaleString("fa-IR")}</p></article>)}
      </section>

      <section className="space-y-4 rounded-3xl border border-amber-900/40 bg-slate-900 p-5 sm:p-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-bold text-white">هشدار موجودی کم</h2>
            <p className="mt-1 text-sm text-slate-400">محصولات فعال با موجودی کمتر یا برابر حد انتخابی</p>
          </div>
          <label className="flex items-center gap-2 text-sm text-slate-300">
            هشدار در موجودی تا
            <input
              type="number"
              min={0}
              max={100000}
              value={lowStockThreshold}
              onChange={(event) => {
                const next = Math.max(0, Math.min(100000, Number(event.target.value) || 0));
                setLowStockThreshold(next);
                try { localStorage.setItem("ecommerce_low_stock_threshold", String(next)); } catch { /* Preference stays in memory for this visit. */ }
              }}
              aria-label="حد هشدار موجودی کم"
              className="w-24 rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-white"
            />
          </label>
        </div>
        {summaryLoading ? (
          <p aria-live="polite" className="py-4 text-sm text-slate-400">در حال بررسی موجودی محصولات...</p>
        ) : lowStockProducts.length === 0 ? (
          <p className="rounded-2xl border border-emerald-900/40 bg-emerald-950/20 p-4 text-sm text-emerald-300">محصول فعالی زیر این حد موجودی نیست.</p>
        ) : (
          <>
            <p role="status" className="text-sm text-amber-300">{lowStockProducts.length.toLocaleString("fa-IR")} محصول نیاز به بررسی دارد.</p>
            <ul className="divide-y divide-slate-800 rounded-2xl border border-slate-800">
              {lowStockProducts.slice(0, 8).map((product) => (
                <li key={product.id} className="flex items-center justify-between gap-4 p-3 text-sm">
                  <Link to="/admin/products" className="min-w-0 truncate text-slate-200 hover:text-white">{product.name}</Link>
                  <span className="shrink-0 font-semibold text-amber-300">{product.available_stock.toLocaleString("fa-IR")} عدد</span>
                </li>
              ))}
            </ul>
            <Link to="/admin/products" className="inline-flex text-sm text-blue-300 hover:text-blue-200">رفتن به مدیریت محصولات</Link>
          </>
        )}
      </section>

      <section className="space-y-4">
        <header><h2 className="text-2xl font-bold text-white">آمار فروش و سفارش‌ها</h2><p className="mt-1 text-sm text-slate-400">گزارش فروش بر اساس پرداخت‌های موفق</p></header>
        <div role="tablist" aria-label="بخش‌های آمار فروش و سفارش‌ها" className="flex flex-wrap gap-2">
          {TABS.map((item) => <button key={item.id} type="button" role="tab" aria-selected={tab === item.id} onClick={() => setTab(item.id)} className={`rounded-2xl border px-5 py-3 text-sm font-semibold backdrop-blur-xl transition ${tab === item.id ? "border-cyan-200/40 bg-cyan-200/15 text-cyan-100 shadow-lg shadow-cyan-950/30" : "border-white/10 bg-white/[0.04] text-slate-300 hover:bg-white/[0.09] hover:text-white"}`}>{item.label}</button>)}
        </div>

        <div role="tabpanel" className="min-h-80 rounded-3xl border border-white/10 bg-white/[0.035] p-5 shadow-2xl shadow-black/20 backdrop-blur-xl sm:p-7">
          <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
            <div><h3 className="text-lg font-bold text-white">{TABS.find((item) => item.id === tab)?.label}</h3><p className="mt-1 text-sm text-slate-400">{tab === "periods" ? "مقایسه‌ی فروش در بازه‌های زمانی" : `گزارش ${PERIODS.find((item) => item.id === period)?.label} اخیر`}</p></div>
            {tab === "periods" ? <div className="w-full space-y-4"><div role="tablist" aria-label="بازه گزارش فروش" className="flex gap-2">{GROUPS.map((item) => <button key={item.id} type="button" role="tab" aria-selected={groupBy === item.id} onClick={() => setGroupBy(item.id)} className={`rounded-xl border px-4 py-2 text-sm transition focus:outline-none focus:ring-2 focus:ring-cyan-300 ${groupBy === item.id ? "border-cyan-200/40 bg-cyan-200/10 text-cyan-100" : "border-white/10 bg-white/[0.03] text-slate-400 hover:text-white"}`}>{item.label}</button>)}</div><div className="grid gap-3 rounded-2xl border border-white/10 bg-slate-950/40 p-4 sm:grid-cols-2"><CalendarDateInput label="از تاریخ" value={reportFrom} onChange={(value) => setReportFrom(value?.slice(0, 10) ?? "")} /><CalendarDateInput label="تا تاریخ" value={reportTo} onChange={(value) => setReportTo(value?.slice(0, 10) ?? "")} /></div>{!rangeIsOrdered && <p role="alert" className="text-sm text-red-300">تاریخ شروع باید قبل از تاریخ پایان باشد.</p>}{rangeTooLarge && <p role="alert" className="text-sm text-amber-300">بازه‌ی انتخابی بیشتر از ۳۶۶ دوره است؛ تاریخ‌ها یا نوع بازه را تغییر بده.</p>}</div> : <select value={period} onChange={(event) => setPeriod(event.target.value as AnalyticsPeriod)} aria-label="بازه‌ی گزارش" className="rounded-xl border border-white/10 bg-slate-900/80 px-4 py-2.5 text-sm text-slate-200">{PERIODS.map((item) => <option key={item.id} value={item.id}>{item.label} اخیر</option>)}</select>}
          </div>
          {error && <div role="alert" className="mb-5 rounded-2xl border border-red-900/50 bg-red-950/30 p-4 text-sm text-red-300"><p>{error}</p><button type="button" onClick={() => setRetry((value) => value + 1)} className="mt-2 underline">تلاش دوباره</button></div>}
          {loading ? <div aria-live="polite" className="flex min-h-64 items-center justify-center text-slate-400">در حال دریافت گزارش...</div> : error ? null : tab === "chart" ? <SalesChart stats={stats} formatDate={formatDate} /> : tab === "products" ? <ProductSalesTable items={products} /> : !rangeIsValid ? null : <TimelineReport items={filteredTimeline} groupBy={groupBy} formatPeriod={formatPeriod} onExport={(items) => downloadSalesCsv(items, groupBy, reportFrom, reportTo)} />}
        </div>
      </section>
    </div>
  );
}

function SalesChart({ stats, formatDate }: { stats: DashboardStats | null; formatDate: (value: string | Date | null | undefined, options?: Intl.DateTimeFormatOptions) => string }) {
  const chart = useMemo(() => {
    const rows = stats?.trend ?? [];
    const values = rows.map((row) => Number(row.revenue) || 0);
    const max = Math.max(...values, 1);
    const width = 900;
    const height = 280;
    const coords = values.map((value, index) => ({
      x: rows.length < 2 ? width / 2 : 24 + (index * (width - 48)) / (rows.length - 1),
      y: height - 24 - (value / max) * (height - 48),
      value,
      date: rows[index].date,
    }));
    return { rows, coords, max, width, height };
  }, [stats]);

  if (!chart.rows.length) return <Empty>برای این بازه داده‌ای ثبت نشده است.</Empty>;
  const polyline = chart.coords.map((point) => `${point.x},${point.y}`).join(" ");
  const area = `${chart.coords[0].x},${chart.height - 24} ${polyline} ${chart.coords[chart.coords.length - 1].x},${chart.height - 24}`;
  return <div className="space-y-5"><div className="grid gap-3 sm:grid-cols-3"><Metric label="درآمد بازه" value={money(stats?.total_revenue ?? 0)} /><Metric label="کل سفارش‌ها" value={(stats?.total_orders ?? 0).toLocaleString("fa-IR")} /><Metric label="سفارش‌های پرداخت‌شده" value={(stats?.paid_orders ?? 0).toLocaleString("fa-IR")} /></div><div className="rounded-2xl border border-white/5 bg-slate-950/40 p-4 sm:p-5"><div className="mb-3 flex justify-between text-xs text-slate-500"><span>{money(chart.max)}</span><span>درآمد روزانه</span></div><svg role="img" aria-label="نمودار روزانه‌ی درآمد فروش" viewBox={`0 0 ${chart.width} ${chart.height}`} preserveAspectRatio="none" className="h-64 w-full overflow-visible"><defs><linearGradient id="sales-fill" x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stopColor="#67e8f9" stopOpacity=".28"/><stop offset="100%" stopColor="#67e8f9" stopOpacity="0"/></linearGradient></defs>{[0,1,2,3].map((index)=><line key={index} x1="0" x2={chart.width} y1={24+index*77} y2={24+index*77} stroke="rgba(148,163,184,.14)" strokeDasharray="4 7"/>)}{chart.coords.length>1&&<polygon points={area} fill="url(#sales-fill)"/>}{chart.coords.length>1&&<polyline points={polyline} fill="none" stroke="#67e8f9" strokeWidth="4" strokeLinejoin="round" strokeLinecap="round" vectorEffect="non-scaling-stroke"/>}{chart.coords.map((point)=><circle key={point.date} cx={point.x} cy={point.y} r="4" fill="#cffafe" stroke="#0f172a" strokeWidth="2"><title>{`${formatDate(point.date)}: ${money(point.value)}`}</title></circle>)}</svg><div className="flex justify-between text-xs text-slate-500"><span>{formatDate(chart.rows[0].date)}</span><span>{formatDate(chart.rows[chart.rows.length-1].date)}</span></div></div></div>;
}

function ProductSalesTable({ items }: { items: ProductSalesItem[] }) {
  if (!items.length) return <Empty>برای این بازه فروش محصولی ثبت نشده است.</Empty>;
  const maxQuantity = Math.max(...items.map((item) => item.quantity_sold), 1);
  return <div className="overflow-x-auto rounded-2xl border border-white/5"><table className="w-full min-w-[700px] text-right text-sm"><thead className="bg-white/[0.04] text-slate-400"><tr><th className="p-4">رتبه</th><th className="p-4">محصول</th><th className="p-4">تعداد فروخته‌شده</th><th className="p-4">تعداد سفارش</th><th className="p-4">مبلغ فروش</th></tr></thead><tbody>{items.map((item,index)=><tr key={item.product_id} className="border-t border-white/5 text-slate-300"><td className="p-4 text-slate-500">{(index+1).toLocaleString("fa-IR")}</td><td className="p-4"><p className="font-medium text-white">{item.product_name}</p><div className="mt-2 h-1.5 max-w-64 overflow-hidden rounded-full bg-slate-800"><div className="h-full rounded-full bg-cyan-400" style={{width:`${Math.max(3,(item.quantity_sold/maxQuantity)*100)}%`}}/></div></td><td className="p-4">{item.quantity_sold.toLocaleString("fa-IR")}</td><td className="p-4">{item.order_count.toLocaleString("fa-IR")}</td><td className="p-4 text-cyan-200">{money(item.revenue)}</td></tr>)}</tbody></table></div>;
}

function TimelineReport({ items, groupBy, formatPeriod, onExport }: { items: SalesTimelineItem[]; groupBy: SalesGroupBy; formatPeriod: (value: string, groupBy: "day" | "month" | "year") => string; onExport: (items: SalesTimelineItem[]) => void }) {
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const sortedItems = useMemo(() => [...items].sort((a, b) => sortOrder === "asc" ? a.period.localeCompare(b.period) : b.period.localeCompare(a.period)), [items, sortOrder]);
  if (!items.length) return <Empty>برای این بازه داده‌ای ثبت نشده است.</Empty>;
  const totalRevenue = items.reduce((sum,item)=>sum+Number(item.revenue||0),0);
  const totalOrders = items.reduce((sum,item)=>sum+item.orders,0);
  const totalUnits = items.reduce((sum,item)=>sum+item.units_sold,0);
  const label = groupBy === "day" ? "روز" : groupBy === "month" ? "ماه" : "سال";
  return <div className="space-y-5"><div className="grid gap-3 sm:grid-cols-3"><Metric label="مجموع فروش" value={money(totalRevenue)} /><Metric label="تعداد سفارش‌ها" value={totalOrders.toLocaleString("fa-IR")} /><Metric label="تعداد کالای فروخته‌شده" value={totalUnits.toLocaleString("fa-IR")} /></div><div className="overflow-hidden rounded-2xl border border-white/5"><div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/5 p-3"><button type="button" onClick={() => onExport(sortedItems)} className="rounded-lg border border-cyan-200/20 bg-cyan-200/10 px-3 py-2 text-xs font-semibold text-cyan-100 hover:bg-cyan-200/15">دریافت CSV</button><label className="flex items-center gap-2 text-xs text-slate-400">مرتب‌سازی تاریخ<select value={sortOrder} onChange={(event) => setSortOrder(event.target.value as "asc" | "desc")} aria-label="مرتب‌سازی گزارش بر اساس تاریخ" className="rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-slate-200"><option value="desc">جدیدترین اول</option><option value="asc">قدیمی‌ترین اول</option></select></label></div><div className="overflow-x-auto"><table className="w-full min-w-[580px] text-right text-sm"><thead className="bg-white/[0.04] text-slate-400"><tr><th className="p-4">{label}</th><th className="p-4">سفارش‌ها</th><th className="p-4">تعداد فروش</th><th className="p-4">درآمد</th></tr></thead><tbody>{sortedItems.map((item)=><tr key={item.period} className="border-t border-white/5 text-slate-300"><td className="p-4 font-medium text-white">{formatPeriod(item.period, groupBy)}</td><td className="p-4">{item.orders.toLocaleString("fa-IR")}</td><td className="p-4">{item.units_sold.toLocaleString("fa-IR")}</td><td className="p-4 text-cyan-200">{money(item.revenue)}</td></tr>)}</tbody></table></div></div></div>;
}

function Metric({ label, value }: { label: string; value: string }) {
  return <article className="rounded-2xl border border-white/5 bg-white/[0.035] p-4"><p className="text-xs text-slate-500">{label}</p><p className="mt-2 font-bold text-white">{value}</p></article>;
}

function Empty({ children }: { children: string }) {
  return <div className="flex min-h-52 items-center justify-center rounded-2xl border border-dashed border-white/10 text-sm text-slate-500">{children}</div>;
}
