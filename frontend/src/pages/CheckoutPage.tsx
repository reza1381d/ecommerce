import { useEffect, useState, type FormEvent, type ReactNode } from "react";
import { Link, useNavigate } from "react-router-dom";
import { createAddress, getAddresses, type Address, type AddressInput } from "../api/addresses";
import { checkout } from "../api/orders";
import { validateCoupon, type CouponQuote } from "../api/coupons";
import { useAuth } from "../context/AuthContext";
import { useCart } from "../context/CartContext";
import { formatMoney } from "../utils/currency";

const EMPTY_ADDRESS: AddressInput = {
  title: "",
  recipient_name: "",
  phone: "",
  province: "",
  city: "",
  address_line: "",
  postal_code: "",
};

export default function CheckoutPage() {
  const { token } = useAuth();
  const { cart, loading: cartLoading, refresh } = useCart();
  const navigate = useNavigate();
  const [addresses, setAddresses] = useState<Address[]>([]);
  const [selectedAddressId, setSelectedAddressId] = useState("");
  const [address, setAddress] = useState<AddressInput>(EMPTY_ADDRESS);
  const [showAddressForm, setShowAddressForm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [couponCode, setCouponCode] = useState("");
  const [appliedCouponCode, setAppliedCouponCode] = useState("");
  const [couponQuote, setCouponQuote] = useState<CouponQuote | null>(null);
  const [couponBusy, setCouponBusy] = useState(false);

  async function handleApplyCoupon(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token || !couponCode.trim()) {
      setError("کد کوپن را وارد کنید.");
      return;
    }

    setCouponBusy(true);
    setError("");
    try {
      const quote = await validateCoupon(token, couponCode.trim().toUpperCase());
      setCouponQuote(quote);
      setAppliedCouponCode(couponCode.trim().toUpperCase());
    } catch (err) {
      setCouponQuote(null);
      setAppliedCouponCode("");
      setError(err instanceof Error ? err.message : "اعتبارسنجی کوپن انجام نشد.");
    } finally {
      setCouponBusy(false);
    }
  }

  useEffect(() => {
    let active = true;

    async function loadAddresses() {
      if (!token) {
        setLoading(false);
        return;
      }

      try {
        const result = await getAddresses(token);
        if (!active) return;
        setAddresses(result);
        const defaultAddress = result.find((item) => item.is_default) ?? result[0];
        if (defaultAddress) setSelectedAddressId(String(defaultAddress.id));
        if (result.length === 0) setShowAddressForm(true);
      } catch (err) {
        if (active) {
          setError(err instanceof Error ? err.message : "دریافت نشانی‌ها انجام نشد.");
        }
      } finally {
        if (active) setLoading(false);
      }
    }

    void loadAddresses();
    return () => {
      active = false;
    };
  }, [token]);

  async function handleCreateAddress(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token) return;
    setSubmitting(true);
    setError("");

    try {
      const created = await createAddress(token, address);
      setAddresses((current) => [...current, created]);
      setSelectedAddressId(String(created.id));
      setAddress(EMPTY_ADDRESS);
      setShowAddressForm(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "ثبت نشانی انجام نشد.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleCheckout() {
    if (!token || !selectedAddressId) {
      setError("یک نشانی برای سفارش انتخاب کنید.");
      return;
    }
    if (couponBusy || (couponCode.trim() && appliedCouponCode !== couponCode.trim().toUpperCase())) {
      setError("ابتدا کد کوپن را اعمال کنید یا آن را حذف کنید.");
      return;
    }

    setSubmitting(true);
    setError("");

    try {
      const order = await checkout(token, Number(selectedAddressId), appliedCouponCode || undefined);
      void refresh().catch(() => undefined);
      navigate("/orders", {
        replace: true,
        state: { createdOrderId: order.id },
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "ثبت سفارش انجام نشد.");
    } finally {
      setSubmitting(false);
    }
  }

  if (cartLoading || loading) {
    return <StatusBox>در حال آماده‌سازی تسویه‌حساب...</StatusBox>;
  }

  if (!cart?.items.length) {
    return (
      <StatusBox>
        <h1 className="text-xl font-bold text-white">سبد خرید خالی است</h1>
        <Link to="/products" className="mt-4 text-blue-400">مشاهده محصولات</Link>
      </StatusBox>
    );
  }

  return (
    <section className="mx-auto max-w-3xl space-y-8">
      <header>
        <h1 className="text-3xl font-black text-white">ثبت سفارش</h1>
        <p className="mt-2 text-slate-400">نشانی تحویل را انتخاب یا ثبت کنید.</p>
      </header>

      {error && <p role="alert" className="rounded-2xl border border-red-900/50 bg-red-950/30 p-4 text-sm text-red-300">{error}</p>}

      {addresses.length > 0 && (
        <fieldset className="space-y-3 rounded-3xl border border-slate-800 bg-slate-900 p-5">
          <legend className="px-2 font-semibold text-white">نشانی‌های ذخیره‌شده</legend>
          {addresses.map((item) => (
            <label key={item.id} className="flex cursor-pointer gap-3 rounded-2xl border border-slate-800 p-4">
              <input
                type="radio"
                name="address"
                value={item.id}
                checked={selectedAddressId === String(item.id)}
                onChange={(event) => setSelectedAddressId(event.target.value)}
              />
              <span className="text-sm leading-6 text-slate-300">
                <strong className="text-white">{item.title}</strong>
                {item.is_default && <span className="mr-2 text-xs text-blue-300">پیش‌فرض</span>}
                <br />
                {item.recipient_name}، {item.province}، {item.city}، {item.address_line}
              </span>
            </label>
          ))}
        </fieldset>
      )}

      {!showAddressForm ? (
        <button
          type="button"
          onClick={() => setShowAddressForm(true)}
          className="rounded-xl border border-slate-700 px-4 py-2 text-sm text-slate-200 hover:bg-slate-800"
        >
          افزودن نشانی جدید
        </button>
      ) : (
        <form onSubmit={handleCreateAddress} className="space-y-4 rounded-3xl border border-slate-800 bg-slate-900 p-5">
          <h2 className="font-semibold text-white">نشانی جدید</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            <AddressField label="عنوان نشانی" value={address.title} onChange={(value) => setAddress({ ...address, title: value })} />
            <AddressField label="نام گیرنده" value={address.recipient_name} onChange={(value) => setAddress({ ...address, recipient_name: value })} />
            <AddressField label="تلفن" value={address.phone} onChange={(value) => setAddress({ ...address, phone: value })} type="tel" />
            <AddressField label="استان" value={address.province} onChange={(value) => setAddress({ ...address, province: value })} />
            <AddressField label="شهر" value={address.city} onChange={(value) => setAddress({ ...address, city: value })} />
            <AddressField label="کد پستی" value={address.postal_code} onChange={(value) => setAddress({ ...address, postal_code: value })} />
          </div>
          <label className="block text-sm text-slate-300">
            نشانی کامل
            <textarea
              required
              maxLength={1000}
              value={address.address_line}
              onChange={(event) => setAddress({ ...address, address_line: event.target.value })}
              className="mt-2 min-h-24 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none focus:border-blue-500"
            />
          </label>
          <button disabled={submitting} className="rounded-xl bg-slate-700 px-4 py-2 text-sm text-white disabled:opacity-50">
            {submitting ? "در حال ذخیره..." : "ذخیره نشانی"}
          </button>
        </form>
      )}

      <section className="space-y-4 rounded-3xl border border-slate-800 bg-slate-900 p-5">
        <div>
          <h2 className="font-semibold text-white">کد تخفیف</h2>
          <p className="mt-1 text-sm text-slate-400">کد کوپن را وارد کنید تا اعتبار و مبلغ تخفیف بررسی شود.</p>
        </div>
        <form onSubmit={handleApplyCoupon} className="flex flex-col gap-3 sm:flex-row">
          <input
            value={couponCode}
            onChange={(event) => {
              setCouponCode(event.target.value.toUpperCase());
              setCouponQuote(null);
              setAppliedCouponCode("");
            }}
            maxLength={100}
            placeholder="مثلاً: OFF20"
            aria-label="کد کوپن"
            className="min-w-0 flex-1 rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none focus:border-blue-500"
          />
          <button
            type="submit"
            disabled={couponBusy || !couponCode.trim()}
            className="rounded-xl border border-blue-500/50 px-5 py-3 font-semibold text-blue-300 hover:bg-blue-500/10 disabled:opacity-50"
          >
            {couponBusy ? "در حال بررسی..." : appliedCouponCode ? "بررسی دوباره" : "اعمال کوپن"}
          </button>
          {appliedCouponCode && (
            <button
              type="button"
              onClick={() => { setCouponCode(""); setAppliedCouponCode(""); setCouponQuote(null); }}
              className="rounded-xl px-3 py-3 text-sm text-slate-400 hover:text-white"
            >
              حذف
            </button>
          )}
        </form>
        {couponQuote && appliedCouponCode && (
          <div aria-live="polite" className="space-y-2 rounded-2xl border border-emerald-900/60 bg-emerald-950/20 p-4 text-sm">
            <p className="font-semibold text-emerald-300">کوپن {appliedCouponCode} اعمال شد.</p>
            <p className="flex justify-between text-slate-300"><span>جمع سبد</span><span>{formatMoney(couponQuote.subtotal)}</span></p>
            <p className="flex justify-between text-emerald-300"><span>تخفیف</span><span>− {formatMoney(couponQuote.discount_amount)}</span></p>
            <p className="flex justify-between border-t border-emerald-900/50 pt-2 font-bold text-white"><span>مبلغ پس از تخفیف</span><span>{formatMoney(couponQuote.total_amount)}</span></p>
          </div>
        )}
      </section>

      {addresses.length > 0 && (
        <div className="flex flex-col gap-4 rounded-3xl border border-slate-800 bg-slate-900 p-5 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-sm text-slate-400">
            با ثبت سفارش، سبد به سفارش تبدیل می‌شود و موجودی برای پرداخت رزرو خواهد شد.
          </p>
          <button
            type="button"
            disabled={submitting || couponBusy || !selectedAddressId}
            onClick={() => void handleCheckout()}
            className="shrink-0 rounded-xl bg-blue-600 px-5 py-3 font-semibold text-white hover:bg-blue-500 disabled:opacity-50"
          >
            {submitting ? "در حال ثبت سفارش..." : "ثبت سفارش"}
          </button>
        </div>
      )}
    </section>
  );
}

function AddressField({
  label,
  value,
  onChange,
  type = "text",
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: string;
}) {
  return (
    <label className="block text-sm text-slate-300">
      {label}
      <input
        required
        type={type}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none focus:border-blue-500"
      />
    </label>
  );
}

function StatusBox({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-48 flex-col items-center justify-center rounded-3xl border border-slate-800 bg-slate-900 p-8 text-center text-slate-400">
      {children}
    </div>
  );
}
