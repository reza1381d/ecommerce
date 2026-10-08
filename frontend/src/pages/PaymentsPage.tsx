import { useEffect, useState, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { getPayments, type Payment } from "../api/payments";
import { useAuth } from "../context/AuthContext";
import { formatMoney } from "../utils/currency";

export default function PaymentsPage() {
  const { token } = useAuth();
  const [payments, setPayments] = useState<Payment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    async function loadPayments() {
      if (!token) {
        setLoading(false);
        return;
      }

      try {
        const result = await getPayments(token);
        if (active) setPayments(result);
      } catch (err) {
        if (active) {
          setError(err instanceof Error ? err.message : "دریافت پرداخت‌ها انجام نشد.");
        }
      } finally {
        if (active) setLoading(false);
      }
    }

    void loadPayments();
    return () => {
      active = false;
    };
  }, [token]);

  return (
    <section className="space-y-8">
      <header>
        <h1 className="text-3xl font-black text-white">پرداخت‌های من</h1>
        <p className="mt-2 text-slate-400">تراکنش‌های سفارش‌های خودت</p>
      </header>

      {error && <p role="alert" className="rounded-2xl border border-red-900/50 bg-red-950/30 p-4 text-red-300">{error}</p>}

      {loading ? (
        <StatusBox>در حال دریافت پرداخت‌ها...</StatusBox>
      ) : payments.length === 0 ? (
        <StatusBox>
          <p>پرداختی برای نمایش وجود ندارد.</p>
          <Link to="/orders" className="mt-4 text-blue-400">رفتن به سفارش‌ها</Link>
        </StatusBox>
      ) : (
        <div className="overflow-x-auto rounded-3xl border border-slate-800 bg-slate-900">
          <table className="w-full min-w-[36rem] text-right text-sm">
            <thead className="border-b border-slate-800 text-slate-400">
              <tr>
                <th className="p-4">شناسه پرداخت</th>
                <th className="p-4">سفارش</th>
                <th className="p-4">مبلغ</th>
                <th className="p-4">وضعیت</th>
                <th className="p-4">درگاه</th>
              </tr>
            </thead>
            <tbody>
              {payments.map((payment) => (
                <tr key={payment.id} className="border-b border-slate-800/70 text-slate-200 last:border-0">
                  <td className="p-4">#{payment.id.toLocaleString("fa-IR")}</td>
                  <td className="p-4">#{payment.order_id.toLocaleString("fa-IR")}</td>
                  <td className="p-4">{formatMoney(payment.amount)}</td>
                  <td className="p-4">{payment.status}</td>
                  <td className="p-4">{payment.provider}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="border-t border-slate-800 px-4 py-3 text-xs text-slate-500">
            پرداخت‌های فعلی backend آزمایشی هستند و با درگاه mock ثبت می‌شوند.
          </p>
        </div>
      )}
    </section>
  );
}

function StatusBox({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-48 flex-col items-center justify-center rounded-3xl border border-slate-800 bg-slate-900 p-8 text-center text-slate-400">
      {children}
    </div>
  );
}
