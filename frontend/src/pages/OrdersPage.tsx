import { useCallback, useEffect, useState, type ReactNode } from "react";
import { Link, useLocation } from "react-router-dom";
import { cancelOrder, getOrders, type Order } from "../api/orders";
import { createPayment, getPayments, type Payment } from "../api/payments";
import { useAuth } from "../context/AuthContext";
import { formatMoney } from "../utils/currency";

const STATUS_LABELS: Record<string, string> = {
  pending_payment: "در انتظار پرداخت",
  paid: "پرداخت‌شده",
  cancelled: "لغوشده",
  shipped: "ارسال‌شده",
  delivered: "تحویل‌شده",
};

export default function OrdersPage() {
  const { token } = useAuth();
  const location = useLocation();
  const createdOrderId = (
    location.state as { createdOrderId?: number } | null
  )?.createdOrderId;

  const [orders, setOrders] = useState<Order[]>([]);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState<number | null>(null);
  const [notice, setNotice] = useState("");

  const loadOrders = useCallback(async () => {
    if (!token) return;

    setLoading(true);
    setError("");
    try {
      const [response, paymentRows] = await Promise.all([
        getOrders(token),
        getPayments(token).catch(() => [] as Payment[]),
      ]);
      setOrders(response.items);
      setPayments(paymentRows);
    } catch (err) {
      setError(err instanceof Error ? err.message : "دریافت سفارش‌ها انجام نشد.");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    void loadOrders();
  }, [loadOrders]);

  async function payOrder(orderId: number) {
    if (!token) return;
    setBusyId(orderId);
    setError("");
    setNotice("");

    try {
      const payment = await createPayment(token, orderId);
      setNotice(`پرداخت سفارش #${orderId} با وضعیت «${payment.status}» ثبت شد.`);
      await loadOrders();
    } catch (err) {
      setError(err instanceof Error ? err.message : "پرداخت سفارش انجام نشد.");
    } finally {
      setBusyId(null);
    }
  }

  async function handleCancel(orderId: number) {
    if (!token || !window.confirm(`سفارش شماره ${orderId.toLocaleString("fa-IR")} لغو شود؟`)) return;
    setBusyId(orderId);
    setError("");
    setNotice("");
    try {
      await cancelOrder(token, orderId);
      setNotice(`سفارش شماره ${orderId.toLocaleString("fa-IR")} لغو شد.`);
      await loadOrders();
    } catch (err) {
      setError(err instanceof Error ? err.message : "لغو سفارش انجام نشد.");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <section className="space-y-8">
      <header>
        <h1 className="text-3xl font-black text-white">سفارش‌های من</h1>
        <p className="mt-2 text-slate-400">وضعیت و جزئیات سفارش‌های ثبت‌شده</p>
      </header>

      {createdOrderId && (
        <p role="status" className="rounded-2xl border border-emerald-900/50 bg-emerald-950/30 p-4 text-sm text-emerald-300">
          سفارش شماره {createdOrderId.toLocaleString("fa-IR")} ثبت شد. برای تکمیل آن، پرداخت را انجام بده.
        </p>
      )}
      {notice && <p role="status" className="rounded-2xl border border-emerald-900/50 bg-emerald-950/30 p-4 text-sm text-emerald-300">{notice}</p>}
      {error && <p role="alert" className="rounded-2xl border border-red-900/50 bg-red-950/30 p-4 text-sm text-red-300">{error}</p>}

      {loading ? (
        <StatusBox>در حال دریافت سفارش‌ها...</StatusBox>
      ) : orders.length === 0 ? (
        <StatusBox>
          <p>هنوز سفارشی ثبت نکرده‌ای.</p>
          <Link to="/products" className="mt-4 text-blue-400">مشاهده محصولات</Link>
        </StatusBox>
      ) : (
        <div className="space-y-5">
          {orders.map((order) => (
            <article key={order.id} className="space-y-5 rounded-3xl border border-slate-800 bg-slate-900 p-5">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 className="font-bold text-white">سفارش #{order.id.toLocaleString("fa-IR")}</h2>
                  <p className="mt-1 text-sm text-slate-400">
                    وضعیت: {STATUS_LABELS[order.status] ?? order.status}
                  </p>
                </div>
                <strong className="text-blue-300">{formatMoney(order.total_amount)}</strong>
              </div>

              <OrderProgress status={order.status} />

              <details className="group rounded-2xl border border-slate-800 bg-slate-950/40">
                <summary className="cursor-pointer list-none px-4 py-3 text-sm font-medium text-slate-300 marker:hidden">جزئیات سفارش و نشانی تحویل <span className="float-left text-slate-500 group-open:rotate-180">⌄</span></summary>
                <div className="space-y-3 border-t border-slate-800 p-4">
                  <div className="space-y-2">
                {order.items.map((item) => (
                  <div key={item.id} className="flex justify-between gap-3 text-sm">
                    <span className="text-slate-300">{item.product_name} × {item.quantity.toLocaleString("fa-IR")}</span>
                    <span className="text-slate-400">{formatMoney(item.total_price)}</span>
                  </div>
                ))}
                  </div>
                  <p className="text-sm leading-6 text-slate-400">تحویل‌گیرنده: {order.address.recipient_name} · {order.address.phone}<br />{order.address.province}، {order.address.city}، {order.address.address_line} · کدپستی {order.address.postal_code}</p>
                  <p className="flex justify-between text-sm text-slate-300"><span>وضعیت پرداخت</span><span>{paymentStatusLabel(payments.filter(payment => payment.order_id === order.id).at(-1)?.status, order.status)}</span></p>
                  <p className="flex justify-between border-t border-slate-800 pt-3 text-sm text-slate-300"><span>جمع کالاها</span><span>{formatMoney(order.subtotal)}</span></p>
                  {Number(order.discount_amount) > 0 && <p className="flex justify-between text-sm text-emerald-300"><span>تخفیف</span><span>− {formatMoney(order.discount_amount)}</span></p>}
                  {Number(order.shipping_amount) > 0 && <p className="flex justify-between text-sm text-slate-300"><span>ارسال</span><span>{formatMoney(order.shipping_amount)}</span></p>}
                  {Number(order.tax_amount) > 0 && <p className="flex justify-between text-sm text-slate-300"><span>مالیات</span><span>{formatMoney(order.tax_amount)}</span></p>}
                </div>
              </details>

              {order.status === "pending_payment" && (
                <div className="flex flex-wrap gap-3">
                  <button
                    type="button"
                    disabled={busyId === order.id}
                    onClick={() => void payOrder(order.id)}
                    className="rounded-xl bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-500 disabled:opacity-50"
                  >
                    {busyId === order.id ? "در حال انجام..." : "پرداخت"}
                  </button>
                  <button
                    type="button"
                    disabled={busyId === order.id}
                    onClick={() => void handleCancel(order.id)}
                    className="rounded-xl border border-slate-700 px-4 py-2 text-sm text-slate-300 hover:bg-slate-800 disabled:opacity-50"
                  >
                    لغو سفارش
                  </button>
                </div>
              )}
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

function paymentStatusLabel(status: string | undefined, orderStatus: string) {
  if (!status) return orderStatus === "pending_payment" ? "پرداخت‌نشده" : orderStatus === "paid" || orderStatus === "shipped" || orderStatus === "delivered" ? "پرداخت‌شده" : "—";
  const labels: Record<string, string> = { successful: "موفق", succeeded: "موفق", pending: "در انتظار پرداخت", failed: "ناموفق", refunded: "بازپرداخت‌شده", cancelled: "لغوشده" };
  return labels[status.toLowerCase()] ?? status;
}

function OrderProgress({ status }: { status: string }) {
  const stages = ["در انتظار پرداخت", "پرداخت‌شده", "ارسال‌شده", "تحویل‌شده"];
  const current = ({ pending_payment: 0, paid: 1, shipped: 2, delivered: 3 } as Record<string, number>)[status];
  if (status === "cancelled" || current === undefined) return <p className="rounded-xl border border-red-900/40 bg-red-950/20 px-4 py-3 text-sm text-red-300">این سفارش لغو شده است.</p>;
  return <ol aria-label="مراحل سفارش" className="grid grid-cols-4 gap-2">{stages.map((stage, index) => <li key={stage} className="flex min-w-0 flex-col items-center gap-2 text-center"><span aria-current={index === current ? "step" : undefined} className={`grid h-7 w-7 place-items-center rounded-full text-xs ${index <= current ? "bg-blue-500 text-white" : "bg-slate-800 text-slate-500"}`}>{index < current ? "✓" : (index + 1).toLocaleString("fa-IR")}</span><span className={`text-[10px] leading-4 sm:text-xs ${index <= current ? "text-slate-200" : "text-slate-500"}`}>{stage}</span></li>)}</ol>;
}

function StatusBox({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-48 flex-col items-center justify-center rounded-3xl border border-slate-800 bg-slate-900 p-8 text-center text-slate-400">
      {children}
    </div>
  );
}
