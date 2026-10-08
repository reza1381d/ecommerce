import { useEffect, useState, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { getProduct, productImageSrc, type Product } from "../api/products";
import { useAuth } from "../context/AuthContext";
import { useCart } from "../context/CartContext";
import { formatMoney } from "../utils/currency";

export default function CartPage() {
  const { token } = useAuth();
  const { cart, loading, error, refresh, updateItem, removeItem } = useCart();
  const [products, setProducts] = useState<Record<number, Product>>({});
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [actionError, setActionError] = useState("");
  const [busyItemId, setBusyItemId] = useState<number | null>(null);

  useEffect(() => {
    let active = true;

    async function loadProductDetails() {
      const items = cart?.items ?? [];
      if (items.length === 0) {
        setProducts({});
        return;
      }

      setDetailsLoading(true);
      try {
        const entries = await Promise.all(
          items.map(async (item) => [
            item.product_id,
            await getProduct(item.product_id),
          ] as const),
        );
        if (active) setProducts(Object.fromEntries(entries));
      } catch (err) {
        if (active) {
          setActionError(
            err instanceof Error ? err.message : "دریافت جزئیات محصول انجام نشد.",
          );
        }
      } finally {
        if (active) setDetailsLoading(false);
      }
    }

    void loadProductDetails();
    return () => {
      active = false;
    };
  }, [cart?.items]);

  const items = cart?.items ?? [];
  const total = items.reduce(
    (sum, item) => sum + (products[item.product_id]?.price ?? 0) * item.quantity,
    0,
  );

  async function changeQuantity(itemId: number, quantity: number) {
    setBusyItemId(itemId);
    setActionError("");
    try {
      if (quantity <= 0) await removeItem(itemId);
      else await updateItem(itemId, quantity);
    } catch (err) {
      setActionError(
        err instanceof Error ? err.message : "به‌روزرسانی سبد انجام نشد.",
      );
    } finally {
      setBusyItemId(null);
    }
  }

  if (!token) {
    return (
      <Notice title="برای مشاهده سبد خرید وارد شوید">
        <Link to="/login" className="mt-4 inline-block rounded-xl bg-blue-600 px-5 py-2.5 text-white">
          ورود به حساب
        </Link>
      </Notice>
    );
  }

  return (
    <section className="space-y-8">
      <header>
        <h1 className="text-3xl font-black text-white">سبد خرید</h1>
        <p className="mt-2 text-slate-400">محصولات انتخاب‌شده را بررسی کنید.</p>
      </header>

      {(error || actionError) && (
        <div role="alert" className="rounded-2xl border border-red-900/50 bg-red-950/30 p-4 text-sm text-red-300">
          {actionError || error}
          <button
            type="button"
            onClick={() => void refresh().catch(() => undefined)}
            className="mr-3 underline"
          >
            تلاش دوباره
          </button>
        </div>
      )}

      {loading || detailsLoading ? (
        <Notice>در حال دریافت سبد خرید...</Notice>
      ) : items.length === 0 ? (
        <Notice title="سبد خرید خالی است">
          <Link to="/products" className="mt-4 inline-block rounded-xl bg-blue-600 px-5 py-2.5 text-white">
            مشاهده محصولات
          </Link>
        </Notice>
      ) : (
        <div className="grid gap-6 lg:grid-cols-[1fr_20rem]">
          <div className="space-y-4">
            {items.map((item) => {
              const product = products[item.product_id];
              const busy = busyItemId === item.id;

              return (
                <article key={item.id} className="flex flex-col gap-4 rounded-3xl border border-slate-800 bg-slate-900 p-5 sm:flex-row sm:items-center">
                  <Link to={`/products/${item.product_id}`} aria-label={`نمایش ${product?.name ?? "محصول"}`} className="flex h-24 w-24 shrink-0 items-center justify-center overflow-hidden rounded-2xl bg-slate-800 text-center text-xs text-slate-500">
                    {product?.image_url ? <img src={productImageSrc(product.image_url)} alt={product.name} className="h-full w-full object-cover" loading="lazy" /> : "بدون تصویر"}
                  </Link>
                  <div className="min-w-0 flex-1">
                    <Link to={`/products/${item.product_id}`} className="font-bold text-white hover:text-blue-300">
                      {product?.name ?? `محصول شماره ${item.product_id}`}
                    </Link>
                    <p className="mt-2 text-sm text-slate-400">
                      {product ? formatMoney(product.price) : "قیمت در دسترس نیست"}
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <button type="button" disabled={busy} onClick={() => void changeQuantity(item.id, item.quantity - 1)} aria-label="کم کردن تعداد" className="h-9 w-9 rounded-lg border border-slate-700 text-white disabled:opacity-50">−</button>
                    <span className="min-w-8 text-center text-white">{item.quantity.toLocaleString("fa-IR")}</span>
                    <button type="button" disabled={busy} onClick={() => void changeQuantity(item.id, item.quantity + 1)} aria-label="زیاد کردن تعداد" className="h-9 w-9 rounded-lg border border-slate-700 text-white disabled:opacity-50">+</button>
                  </div>
                  <button type="button" disabled={busy} onClick={() => void changeQuantity(item.id, 0)} className="text-sm text-red-300 hover:text-red-200 disabled:opacity-50">
                    حذف
                  </button>
                </article>
              );
            })}
          </div>

          <aside className="h-fit space-y-5 rounded-3xl border border-slate-800 bg-slate-900 p-6">
            <h2 className="text-lg font-bold text-white">خلاصه سفارش</h2>
            <div className="flex justify-between text-slate-400">
              <span>جمع محصولات</span>
              <span>{formatMoney(total)}</span>
            </div>
            <p className="text-xs leading-6 text-slate-500">
              هزینه نهایی و موجودی هنگام ثبت سفارش توسط سرور محاسبه می‌شود.
            </p>
            <Link to="/checkout" className="block rounded-xl bg-blue-600 px-5 py-3 text-center font-semibold text-white hover:bg-blue-500">
              ادامه و انتخاب نشانی
            </Link>
          </aside>
        </div>
      )}
    </section>
  );
}

function Notice({ title, children }: { title?: string; children?: ReactNode }) {
  return (
    <div className="flex min-h-48 flex-col items-center justify-center rounded-3xl border border-slate-800 bg-slate-900 p-8 text-center text-slate-400">
      {title && <h2 className="text-xl font-bold text-white">{title}</h2>}
      {children}
    </div>
  );
}
