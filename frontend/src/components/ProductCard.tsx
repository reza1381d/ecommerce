import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { productImageSrc, type Product } from "../api/products";
import { useAuth } from "../context/AuthContext";
import { useCart } from "../context/CartContext";
import { useFavorites } from "../context/FavoritesContext";
import { formatMoney } from "../utils/currency";

export default function ProductCard({ product }: { product: Product }) {
  const { isAuthenticated } = useAuth();
  const { addItem } = useCart();
  const { isFavorite, toggleFavorite } = useFavorites();
  const location = useLocation();
  const navigate = useNavigate();
  const [message, setMessage] = useState("");
  const [adding, setAdding] = useState(false);
  const [imageFailed, setImageFailed] = useState(false);

  async function handleAddToCart() {
    setMessage("");

    if (!isAuthenticated) {
      navigate("/login", { state: { from: location } });
      return;
    }

    setAdding(true);

    try {
      await addItem(product.id);
      setMessage("به سبد خرید اضافه شد.");
    } catch (err) {
      setMessage(
        err instanceof Error ? err.message : "افزودن به سبد خرید انجام نشد.",
      );
    } finally {
      setAdding(false);
    }
  }

  return (
    <article className="overflow-hidden rounded-3xl border border-slate-800 bg-slate-900 transition hover:-translate-y-1 hover:border-slate-700">
      <div className="relative">
        <Link
          to={`/products/${product.id}`}
          className="flex h-48 items-center justify-center bg-slate-800 text-sm text-slate-500"
          aria-label={`جزئیات ${product.name}`}
        >
          {product.image_url && !imageFailed ? <img src={productImageSrc(product.image_url)} alt={product.name} onError={() => setImageFailed(true)} className="h-full w-full object-cover" loading="lazy" /> : "تصویر محصول در دسترس نیست"}
        </Link>
        <button
          type="button"
          onClick={() => toggleFavorite(product.id)}
          aria-pressed={isFavorite(product.id)}
          aria-label={isFavorite(product.id) ? `حذف ${product.name} از علاقه‌مندی‌ها` : `افزودن ${product.name} به علاقه‌مندی‌ها`}
          title={isFavorite(product.id) ? "حذف از علاقه‌مندی‌ها" : "افزودن به علاقه‌مندی‌ها"}
          className="absolute left-3 top-3 grid h-10 w-10 place-items-center rounded-full border border-white/15 bg-slate-950/75 text-xl text-white shadow-lg backdrop-blur transition hover:scale-105 hover:bg-slate-900"
        >
          <span aria-hidden="true" className={isFavorite(product.id) ? "text-rose-400" : "text-slate-200"}>{isFavorite(product.id) ? "♥" : "♡"}</span>
        </button>
      </div>

      <div className="space-y-4 p-5">
        <div>
          <Link
            to={`/products/${product.id}`}
            className="font-bold text-white hover:text-blue-300"
          >
            {product.name}
          </Link>

          {product.description && (
            <p className="mt-2 line-clamp-2 text-sm text-slate-400">
              {product.description}
            </p>
          )}
        </div>

        <div className="flex items-center justify-between gap-3">
          <span className="font-bold text-blue-300">
            {formatMoney(product.price)}
          </span>
          <span
            className={
              product.available_stock > 0
                ? "text-xs text-emerald-400"
                : "text-xs text-slate-500"
            }
          >
            {product.available_stock > 0
              ? `موجودی: ${product.available_stock.toLocaleString("fa-IR")}`
              : "ناموجود"}
          </span>
        </div>

        <button
          type="button"
          onClick={handleAddToCart}
          disabled={adding || product.available_stock <= 0}
          className="w-full rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {adding ? "در حال افزودن..." : "افزودن به سبد"}
        </button>

        {message && (
          <p role="status" aria-live="polite" className={`text-xs ${message.includes("اضافه شد") ? "text-emerald-300" : "text-red-300"}`}>
            {message}
          </p>
        )}
      </div>
    </article>
  );
}
