import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import { getProduct, productImageSrc, type Product } from "../api/products";
import { useAuth } from "../context/AuthContext";
import { useCart } from "../context/CartContext";
import { useFavorites } from "../context/FavoritesContext";
import { formatMoney } from "../utils/currency";

export default function ProductDetailPage() {
  const { productId } = useParams();
  const id = Number(productId);
  const { isAuthenticated } = useAuth();
  const { addItem } = useCart();
  const { isFavorite, toggleFavorite } = useFavorites();
  const location = useLocation();
  const navigate = useNavigate();

  const [product, setProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [adding, setAdding] = useState(false);
  const [imageOpen, setImageOpen] = useState(false);
  const [imageFailed, setImageFailed] = useState(false);

  useEffect(() => {
    let active = true;

    async function loadProduct() {
      if (!Number.isInteger(id) || id <= 0) {
        setError("شناسه محصول معتبر نیست.");
        setLoading(false);
        return;
      }

      setLoading(true);
      setError("");
      setImageFailed(false);
      setImageOpen(false);

      try {
        const result = await getProduct(id);
        if (active) setProduct(result);
      } catch (err) {
        if (active) {
          setError(err instanceof Error ? err.message : "دریافت محصول انجام نشد.");
        }
      } finally {
        if (active) setLoading(false);
      }
    }

    void loadProduct();
    return () => {
      active = false;
    };
  }, [id]);

  useEffect(() => {
    if (!imageOpen) return;
    function onKeyDown(event: KeyboardEvent) { if (event.key === "Escape") setImageOpen(false); }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [imageOpen]);

  async function handleAdd() {
    if (!product) return;

    if (!isAuthenticated) {
      navigate("/login", { state: { from: location } });
      return;
    }

    setAdding(true);
    setMessage("");

    try {
      await addItem(product.id);
      setMessage("محصول به سبد خرید اضافه شد.");
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "افزودن به سبد انجام نشد.");
    } finally {
      setAdding(false);
    }
  }

  if (loading) {
    return <PageMessage>در حال دریافت اطلاعات محصول...</PageMessage>;
  }

  if (error || !product) {
    return (
      <PageMessage>
        <p role="alert">{error || "محصول پیدا نشد."}</p>
        <Link className="mt-4 inline-block text-blue-400" to="/products">
          بازگشت به محصولات
        </Link>
      </PageMessage>
    );
  }

  return (
    <section className="space-y-8">
      <Link to="/products" className="text-sm text-blue-400 hover:text-blue-300">
        ← بازگشت به محصولات
      </Link>

      <div className="grid gap-8 lg:grid-cols-2">
        <div className="flex min-h-80 items-center justify-center overflow-hidden rounded-3xl border border-slate-800 bg-slate-900 text-slate-500">
          {product.image_url && !imageFailed ? <button type="button" onClick={() => setImageOpen(true)} aria-label={`بزرگ‌نمایی تصویر ${product.name}`} className="group relative flex h-full min-h-80 w-full items-center justify-center"><img src={productImageSrc(product.image_url)} alt={product.name} onError={() => setImageFailed(true)} className="max-h-[34rem] w-full object-contain" /><span className="absolute bottom-4 rounded-full bg-black/60 px-3 py-1.5 text-xs text-white opacity-0 transition group-hover:opacity-100 group-focus:opacity-100">برای بزرگ‌نمایی انتخاب کنید</span></button> : <div className="flex min-h-80 items-center justify-center">تصویر محصول در دسترس نیست</div>}
        </div>

        <div className="space-y-6 rounded-3xl border border-slate-800 bg-slate-900 p-6 sm:p-8">
          <div>
            <h1 className="text-3xl font-black text-white">{product.name}</h1>
            {product.description && (
              <p className="mt-4 whitespace-pre-wrap leading-8 text-slate-300">
                {product.description}
              </p>
            )}
          </div>

          <div className="flex flex-wrap items-center justify-between gap-4 border-y border-slate-800 py-5">
            <span className="text-2xl font-bold text-blue-300">
              {formatMoney(product.price)}
            </span>
            <span className={product.available_stock > 0 ? "text-emerald-400" : "text-slate-500"}>
              {product.available_stock > 0
                ? `موجودی: ${product.available_stock.toLocaleString("fa-IR")}`
                : "ناموجود"}
            </span>
          </div>

          <div className="grid gap-3 sm:grid-cols-[1fr_auto]">
            <button
              type="button"
              onClick={handleAdd}
              disabled={adding || product.available_stock <= 0 || !product.is_active}
              className="w-full rounded-2xl bg-blue-600 px-5 py-3 font-semibold text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {adding ? "در حال افزودن..." : "افزودن به سبد خرید"}
            </button>
            <button
              type="button"
              onClick={() => toggleFavorite(product.id)}
              aria-pressed={isFavorite(product.id)}
              className="rounded-2xl border border-slate-700 px-5 py-3 font-semibold text-slate-200 transition hover:border-rose-400/60 hover:text-rose-300"
            >
              {isFavorite(product.id) ? "♥ ذخیره‌شده" : "♡ افزودن به علاقه‌مندی‌ها"}
            </button>
          </div>

          {message && <p aria-live="polite" className="text-sm text-slate-300">{message}</p>}
        </div>
      </div>
      {imageOpen && product.image_url && <div role="dialog" aria-modal="true" aria-label={`تصویر ${product.name}`} onClick={() => setImageOpen(false)} className="fixed inset-0 z-[100] flex items-center justify-center bg-black/90 p-4"><button type="button" autoFocus onClick={() => setImageOpen(false)} aria-label="بستن تصویر" className="absolute left-5 top-5 rounded-full border border-white/20 bg-black/40 px-4 py-2 text-white">بستن ✕</button><img src={productImageSrc(product.image_url)} alt={product.name} onClick={event => event.stopPropagation()} className="max-h-[90vh] max-w-full rounded-2xl object-contain" /></div>}
    </section>
  );
}

function PageMessage({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-[45vh] flex-col items-center justify-center rounded-3xl border border-slate-800 bg-slate-900 p-8 text-center text-slate-300">
      {children}
    </div>
  );
}

