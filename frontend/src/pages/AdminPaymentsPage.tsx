import { useEffect, useState, type FormEvent } from "react";
import {
  getAdminPayments,
  type AdminPayment,
  type AdminPaymentSortBy,
} from "../api/adminPayments";
import { useAuth } from "../context/AuthContext";
import { formatMoney as money } from "../utils/currency";
import { useDateFormat } from "../context/DateFormatContext";

const PAGE_SIZE = 20;
const PAYMENT_LABELS: Record<string, string> = {
  successful: "موفق",
  pending: "در انتظار پرداخت",
  failed: "ناموفق",
  refunded: "بازپرداخت‌شده",
  cancelled: "لغوشده",
};
const ORDER_LABELS: Record<string, string> = {
  pending_payment: "در انتظار پرداخت",
  paid: "پرداخت‌شده",
  shipped: "ارسال‌شده",
  delivered: "تحویل‌شده",
  cancelled: "لغوشده",
};


function paymentStatusClass(status: string) {
  const normalized = status.toLowerCase();
  if (["successful", "succeeded", "completed"].includes(normalized)) {
    return "text-emerald-300";
  }
  if (["failed", "cancelled", "refunded"].includes(normalized)) {
    return "text-red-300";
  }
  return "text-amber-300";
}

export default function AdminPaymentsPage() {
  const { token } = useAuth();
  const { formatDate } = useDateFormat();
  const [payments, setPayments] = useState<AdminPayment[]>([]);
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [paymentStatus, setPaymentStatus] = useState("");
  const [provider, setProvider] = useState("");
  const [sortBy, setSortBy] = useState<AdminPaymentSortBy>("created_at");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    let active = true;
    async function loadPayments() {
      if (!token) return;
      setLoading(true);
      setError("");
      try {
        const result = await getAdminPayments(token, {
          page,
          limit: PAGE_SIZE,
          search,
          paymentStatus: paymentStatus || undefined,
          provider: provider || undefined,
          sortBy,
          sortOrder,
        });
        if (active) {
          setPayments(result.items);
          setTotal(result.total);
        }
      } catch (err) {
        if (active) {
          setPayments([]);
          setTotal(0);
          setError(err instanceof Error ? err.message : "دریافت پرداخت‌ها ناموفق بود.");
        }
      } finally {
        if (active) setLoading(false);
      }
    }
    void loadPayments();
    return () => { active = false; };
  }, [token, page, search, paymentStatus, provider, sortBy, sortOrder, retry]);

  function submitSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPage(1);
    setSearch(searchInput.trim());
  }

  function changeSort(field: AdminPaymentSortBy) {
    if (field === sortBy) {
      setSortOrder((current) => current === "asc" ? "desc" : "asc");
    } else {
      setSortBy(field);
      setSortOrder(field === "amount" || field === "id" || field === "order_id" ? "desc" : "asc");
    }
    setPage(1);
  }

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <section dir="rtl" className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-black text-white">مدیریت پرداخت‌ها</h1>
          <p className="mt-2 text-slate-400">پرداخت‌های مشتریان، سفارش‌های مرتبط و وضعیت تراکنش‌ها</p>
        </div>
        <button type="button" disabled={loading} onClick={() => setRetry((value) => value + 1)} className="rounded-xl border border-slate-700 px-4 py-2 text-sm text-slate-200 hover:bg-slate-800 disabled:opacity-50">به‌روزرسانی</button>
      </header>

      <div className="grid gap-3 rounded-2xl border border-slate-800 bg-slate-900 p-4 lg:grid-cols-[minmax(15rem,1fr)_auto_auto_auto]">
        <form onSubmit={submitSearch} className="flex min-w-0 gap-2">
          <input value={searchInput} onChange={(event) => setSearchInput(event.target.value)} placeholder="جست‌وجو با شناسه، سفارش، مشتری یا کد پیگیری" aria-label="جست‌وجوی پرداخت‌ها" className="min-w-0 flex-1 rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none focus:border-blue-500" />
          <button type="submit" className="rounded-xl bg-blue-600 px-4 text-sm font-medium text-white hover:bg-blue-500">جست‌وجو</button>
        </form>
        <select value={paymentStatus} onChange={(event) => { setPage(1); setPaymentStatus(event.target.value); }} aria-label="فیلتر وضعیت پرداخت" className="rounded-xl border border-slate-700 bg-slate-950 px-3 py-3 text-slate-200">
          <option value="">همه وضعیت‌ها</option>
          <option value="successful">موفق</option>
          <option value="pending">در انتظار پرداخت</option>
          <option value="failed">ناموفق</option>
          <option value="refunded">بازپرداخت‌شده</option>
        </select>
        <select value={provider} onChange={(event) => { setPage(1); setProvider(event.target.value); }} aria-label="فیلتر درگاه پرداخت" className="rounded-xl border border-slate-700 bg-slate-950 px-3 py-3 text-slate-200">
          <option value="">همه درگاه‌ها</option>
          <option value="mock">Mock</option>
        </select>
        <div className="flex gap-2">
          <select value={sortBy} onChange={(event) => changeSort(event.target.value as AdminPaymentSortBy)} aria-label="مرتب‌سازی پرداخت‌ها" className="min-w-0 flex-1 rounded-xl border border-slate-700 bg-slate-950 px-3 py-3 text-slate-200">
            <option value="created_at">تاریخ پرداخت</option>
            <option value="id">شناسه پرداخت</option>
            <option value="order_id">شماره سفارش</option>
            <option value="amount">مبلغ</option>
            <option value="status">وضعیت</option>
            <option value="provider">درگاه</option>
          </select>
          <button type="button" onClick={() => { setPage(1); setSortOrder((value) => value === "asc" ? "desc" : "asc"); }} className="rounded-xl border border-slate-700 px-3 text-sm text-slate-200">{sortOrder === "asc" ? "صعودی" : "نزولی"}</button>
        </div>
      </div>

      {error && <div role="alert" className="rounded-2xl border border-red-900/50 bg-red-950/30 p-4 text-red-300"><p>{error}</p><button type="button" onClick={() => setRetry((value) => value + 1)} className="mt-2 underline">تلاش دوباره</button></div>}
      <div className="flex justify-between text-sm text-slate-400"><span>{total.toLocaleString("fa-IR")} پرداخت</span><span>{loading ? "در حال بارگذاری..." : `صفحه ${page.toLocaleString("fa-IR")} از ${totalPages.toLocaleString("fa-IR")}`}</span></div>

      {loading ? (
        <div aria-live="polite" className="rounded-2xl border border-slate-800 bg-slate-900 p-10 text-center text-slate-400">در حال دریافت پرداخت‌ها...</div>
      ) : payments.length === 0 ? (
        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-10 text-center text-slate-400">پرداختی با این شرایط پیدا نشد.</div>
      ) : (
        <>
        <div className="space-y-3 lg:hidden">{payments.map(payment => <PaymentCard key={payment.id} payment={payment} formatDate={formatDate} />)}</div>
        <div className="hidden overflow-x-auto rounded-2xl border border-slate-800 lg:block">
          <table className="w-full min-w-[1050px] text-right text-sm">
            <thead className="bg-slate-900 text-slate-400"><tr><th className="p-4">پرداخت</th><th className="p-4">مشتری</th><th className="p-4">سفارش</th><th className="p-4">مبلغ</th><th className="p-4">وضعیت پرداخت</th><th className="p-4">درگاه / کد پیگیری</th><th className="p-4">تاریخ</th></tr></thead>
            <tbody>{payments.map((payment) => <PaymentRow key={payment.id} payment={payment} formatDate={formatDate} />)}</tbody>
          </table>
        </div>
        </>
      )}

      {totalPages > 1 && <nav aria-label="صفحه‌بندی پرداخت‌ها" className="flex items-center justify-center gap-3"><button type="button" disabled={page <= 1 || loading} onClick={() => setPage((value) => value - 1)} className="rounded-xl border border-slate-700 px-4 py-2 text-sm disabled:opacity-40">قبلی</button><span className="text-sm text-slate-400">صفحه {page.toLocaleString("fa-IR")} از {totalPages.toLocaleString("fa-IR")}</span><button type="button" disabled={page >= totalPages || loading} onClick={() => setPage((value) => value + 1)} className="rounded-xl border border-slate-700 px-4 py-2 text-sm disabled:opacity-40">بعدی</button></nav>}
    </section>
  );
}

function PaymentCard({ payment, formatDate }: { payment: AdminPayment; formatDate: (value: string | Date | null | undefined, options?: Intl.DateTimeFormatOptions) => string }) {
  const status = payment.status.toLowerCase();
  return <article className="space-y-3 rounded-2xl border border-slate-800 bg-slate-900 p-4 text-sm"><header className="flex items-start justify-between gap-3"><div><p className="font-semibold text-white">پرداخت #{payment.id.toLocaleString("fa-IR")}</p><p className="mt-1 text-xs text-slate-400">سفارش #{payment.order_id.toLocaleString("fa-IR")} · {ORDER_LABELS[payment.order_status] ?? payment.order_status}</p></div><span className={`shrink-0 text-xs ${paymentStatusClass(status)}`}>{PAYMENT_LABELS[status] ?? payment.status}</span></header><p className="text-lg font-bold text-white">{money(payment.amount)}</p><div className="border-t border-slate-800 pt-3 text-xs text-slate-400"><p className="font-medium text-slate-200">{payment.customer.first_name} {payment.customer.last_name}</p><p className="mt-1 break-all">{payment.customer.email}</p><p className="mt-1">{payment.provider} · {payment.provider_payment_id || "بدون کد پیگیری"}</p><p className="mt-2">{formatDate(payment.created_at, { dateStyle: "medium", timeStyle: "short" })}</p></div></article>;
}

function PaymentRow({ payment, formatDate }: { payment: AdminPayment; formatDate: (value: string | Date | null | undefined, options?: Intl.DateTimeFormatOptions) => string }) {
  const status = payment.status.toLowerCase();
  return (
    <tr className="border-t border-slate-800 text-slate-300">
      <td className="p-4 font-medium text-white">#{payment.id.toLocaleString("fa-IR")}</td>
      <td className="p-4"><p className="text-white">{payment.customer.first_name} {payment.customer.last_name}</p><p className="mt-1 text-xs text-slate-500">{payment.customer.email}</p><p className="mt-1 text-xs text-slate-500">{payment.customer.phone || "تلفن ثبت نشده"}</p></td>
      <td className="p-4"><p>#{payment.order_id.toLocaleString("fa-IR")}</p><p className="mt-1 text-xs text-slate-500">{ORDER_LABELS[payment.order_status] ?? payment.order_status}</p></td>
      <td className="p-4 whitespace-nowrap">{money(payment.amount)}</td>
      <td className={`p-4 ${paymentStatusClass(status)}`}>{PAYMENT_LABELS[status] ?? payment.status}</td>
      <td className="p-4"><p>{payment.provider}</p><p className="mt-1 max-w-56 break-all text-xs text-slate-500">{payment.provider_payment_id || "کد پیگیری ندارد"}</p></td>
      <td className="p-4 whitespace-nowrap">{formatDate(payment.created_at, { dateStyle: "medium", timeStyle: "short" })}</td>
    </tr>
  );
}
