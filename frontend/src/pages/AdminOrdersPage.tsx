import { useEffect, useState } from "react";
import { getAdminOrders, type AdminOrder } from "../api/adminOrders";
import { useAuth } from "../context/AuthContext";
import { formatMoney as money } from "../utils/currency";

const PAGE_SIZE = 20;
const ORDER_LABELS: Record<string, string> = {
  pending_payment: "در انتظار پرداخت",
  paid: "پرداخت‌شده",
  shipped: "ارسال‌شده",
  delivered: "تحویل‌شده",
  cancelled: "لغوشده",
};
const PAYMENT_LABELS: Record<string, string> = {
  successful: "موفق",
  pending: "در انتظار پرداخت",
  failed: "ناموفق",
  refunded: "بازپرداخت‌شده",
  unpaid: "پرداخت‌نشده",
};

function PaymentBadge({ order }: { order: AdminOrder }) {
  const status = order.payment_status.toLowerCase();
  const style = ["successful", "succeeded", "completed"].includes(status)
    ? "text-emerald-300"
    : ["failed", "cancelled", "refunded", "unpaid"].includes(status)
      ? "text-red-300"
      : "text-amber-300";

  return (
    <span className={`rounded-full bg-slate-800 px-3 py-1 text-sm ${style}`}>
      {PAYMENT_LABELS[status] ?? order.payment_status}
    </span>
  );
}

export default function AdminOrdersPage() {
  const { token } = useAuth();
  const [orders, setOrders] = useState<AdminOrder[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [orderStatus, setOrderStatus] = useState("");
  const [paymentStatus, setPaymentStatus] = useState("");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [reload, setReload] = useState(0);

  useEffect(() => {
    let active = true;
    async function load() {
      if (!token) return;
      setLoading(true);
      setError("");
      try {
        const result = await getAdminOrders(token, {
          page,
          limit: PAGE_SIZE,
          orderStatus: orderStatus || undefined,
          paymentStatus: paymentStatus || undefined,
        });
        if (active) {
          setOrders(result.items);
          setTotal(result.total);
        }
      } catch (err) {
        if (active) {
          setOrders([]);
          setTotal(0);
          setError(err instanceof Error ? err.message : "دریافت سفارش‌ها ناموفق بود.");
        }
      } finally {
        if (active) setLoading(false);
      }
    }
    void load();
    return () => { active = false; };
  }, [token, page, orderStatus, paymentStatus, reload]);

  const visibleOrders = orders.filter((order) => {
    const term = search.trim().toLocaleLowerCase();
    if (!term) return true;
    const customer = order.customer;
    return [
      String(order.id),
      String(customer.id),
      customer.email,
      customer.first_name,
      customer.last_name,
      order.address.recipient_name,
      order.address.phone,
    ].some((value) => value.toLocaleLowerCase().includes(term));
  });
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  function changeFilter(setter: (value: string) => void, value: string) {
    setter(value);
    setPage(1);
  }

  return (
    <section dir="rtl" className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-black text-white">مدیریت سفارش‌ها</h1>
          <p className="mt-2 text-slate-400">فهرست سفارش‌های مشتریان و وضعیت پرداخت آن‌ها</p>
        </div>
        <button type="button" disabled={loading} onClick={() => setReload((value) => value + 1)} className="rounded-xl border border-slate-700 px-4 py-2 text-sm text-slate-200 hover:bg-slate-800 disabled:opacity-50">
          به‌روزرسانی
        </button>
      </header>

      <div className="grid gap-3 rounded-2xl border border-slate-800 bg-slate-900 p-4 sm:grid-cols-3">
        <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="جست‌وجو با شماره سفارش، مشتری یا تلفن" aria-label="جست‌وجوی سفارش‌ها" className="rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none focus:border-blue-500" />
        <select value={orderStatus} onChange={(event) => changeFilter(setOrderStatus, event.target.value)} aria-label="فیلتر وضعیت سفارش" className="rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-slate-200">
          <option value="">همه وضعیت‌های سفارش</option>
          <option value="pending_payment">در انتظار پرداخت</option>
          <option value="paid">پرداخت‌شده</option>
          <option value="shipped">ارسال‌شده</option>
          <option value="delivered">تحویل‌شده</option>
          <option value="cancelled">لغوشده</option>
        </select>
        <select value={paymentStatus} onChange={(event) => changeFilter(setPaymentStatus, event.target.value)} aria-label="فیلتر وضعیت پرداخت" className="rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-slate-200">
          <option value="">همه وضعیت‌های پرداخت</option>
          <option value="successful">موفق</option>
          <option value="pending">در انتظار پرداخت</option>
          <option value="failed">ناموفق</option>
          <option value="unpaid">پرداخت‌نشده</option>
        </select>
      </div>

      <div className="flex justify-between text-sm text-slate-400">
        <span>{total.toLocaleString("fa-IR")} سفارش</span>
        {totalPages > 1 && <span>صفحه {page.toLocaleString("fa-IR")} از {totalPages.toLocaleString("fa-IR")}</span>}
      </div>

      {error && <div role="alert" className="rounded-2xl border border-red-900/50 bg-red-950/30 p-4 text-red-300"><p>{error}</p><button onClick={() => setReload((value) => value + 1)} className="mt-2 underline">تلاش دوباره</button></div>}
      {loading ? (
        <div aria-live="polite" className="rounded-2xl border border-slate-800 bg-slate-900 p-10 text-center text-slate-400">در حال دریافت سفارش‌ها...</div>
      ) : visibleOrders.length === 0 ? (
        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-10 text-center text-slate-400">سفارشی با این شرایط پیدا نشد.</div>
      ) : (
        <div className="space-y-4">
          {visibleOrders.map((order) => (
            <article key={order.id} className="space-y-4 rounded-2xl border border-slate-800 bg-slate-900 p-5">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <h2 className="font-bold text-white">سفارش #{order.id.toLocaleString("fa-IR")}</h2>
                  <p className="mt-1 text-sm text-slate-400">{order.customer.first_name} {order.customer.last_name} · {order.customer.email}</p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <span className="rounded-full bg-slate-800 px-3 py-1 text-sm text-slate-200">سفارش: {ORDER_LABELS[order.status] ?? order.status}</span>
                  <PaymentBadge order={order} />
                </div>
              </div>

              <div className="grid gap-4 border-y border-slate-800 py-4 md:grid-cols-2">
                <div className="space-y-1 text-sm leading-6 text-slate-300">
                  <p><span className="text-slate-500">گیرنده:</span> {order.address.recipient_name} · {order.address.phone}</p>
                  <p><span className="text-slate-500">نشانی:</span> {order.address.province}، {order.address.city}، {order.address.address_line}، {order.address.postal_code}</p>
                </div>
                <div className="space-y-2 text-sm">
                  {order.items.map((item) => <p key={item.id} className="flex justify-between gap-3 text-slate-300"><span>{item.product_name} × {item.quantity.toLocaleString("fa-IR")}</span><span>{money(item.total_price)}</span></p>)}
                </div>
              </div>

              <div className="flex flex-wrap items-center justify-between gap-3 text-sm">
                <strong className="text-blue-300">مبلغ سفارش: {money(order.total_amount)}</strong>
                {order.latest_payment && <span className="text-slate-400">تراکنش #{order.latest_payment.id.toLocaleString("fa-IR")} · {order.latest_payment.provider} · {money(order.latest_payment.amount)}{order.latest_payment.provider_payment_id ? ` · کد پیگیری ${order.latest_payment.provider_payment_id}` : ""}</span>}
              </div>
            </article>
          ))}
        </div>
      )}

      {totalPages > 1 && <nav aria-label="صفحه‌بندی سفارش‌ها" className="flex items-center justify-center gap-3"><button type="button" disabled={page <= 1 || loading} onClick={() => setPage((value) => value - 1)} className="rounded-xl border border-slate-700 px-4 py-2 text-sm disabled:opacity-40">قبلی</button><span className="text-sm text-slate-400">صفحه {page.toLocaleString("fa-IR")} از {totalPages.toLocaleString("fa-IR")}</span><button type="button" disabled={page >= totalPages || loading} onClick={() => setPage((value) => value + 1)} className="rounded-xl border border-slate-700 px-4 py-2 text-sm disabled:opacity-40">بعدی</button></nav>}
    </section>
  );
}
