import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getProducts, type Product } from "../api/products";
import { useStoreSettings } from "../context/StoreSettingsContext";
import ProductCard from "../components/ProductCard";

const FEATURED_LIMIT = 8;

export default function HomePage() {
  const { settings } = useStoreSettings();
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [retryCount, setRetryCount] = useState(0);

  useEffect(() => {
    let active = true;

    async function loadFeaturedProducts() {
      setLoading(true);
      setError("");
      try {
        const response = await getProducts({
          page: 1,
          limit: FEATURED_LIMIT,
          isActive: true,
        });
        if (active) setProducts(response.items);
      } catch (err) {
        if (active) {
          setProducts([]);
          setError(err instanceof Error ? err.message : "دریافت محصولات انجام نشد.");
        }
      } finally {
        if (active) setLoading(false);
      }
    }

    void loadFeaturedProducts();
    return () => { active = false; };
  }, [retryCount]);

  return (
    <div className="space-y-14">
      <section className="store-hero overflow-hidden rounded-[2rem] border px-6 py-14 sm:px-10 lg:px-14">
        <div className="max-w-2xl">
          <p className="text-sm font-semibold text-blue-300">{settings.homeHeroBadge}</p>
          <h1 className="mt-4 whitespace-pre-line text-4xl font-black leading-tight text-white sm:text-5xl">
            {settings.homeHeroTitle}
          </h1>
          <p className="mt-5 max-w-xl whitespace-pre-line leading-8 text-slate-300">
            {settings.homeHeroDescription}
          </p>
          <Link
            to="/products"
            className="mt-8 inline-flex rounded-2xl bg-blue-600 px-6 py-3 font-semibold text-white transition hover:bg-blue-500"
          >
            {settings.homeHeroButtonLabel}
          </Link>
        </div>
      </section>

      <section className="space-y-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h2 className="text-2xl font-bold text-white">محصولات فروشگاه</h2>
            <p className="mt-2 text-sm text-slate-400">تعدادی از محصولات موجود در فروشگاه</p>
          </div>
          <Link to="/products" className="text-sm font-medium text-blue-400 transition hover:text-blue-300">
            دیدن همه محصولات
          </Link>
        </div>

        {loading ? (
          <div aria-live="polite" className="rounded-3xl border border-slate-800 bg-slate-900 p-10 text-center text-slate-400">
            در حال دریافت محصولات...
          </div>
        ) : error ? (
          <div role="alert" className="rounded-3xl border border-red-900/50 bg-red-950/30 p-8 text-center">
            <p className="text-red-300">{error}</p>
            <button
              type="button"
              onClick={() => setRetryCount((count) => count + 1)}
              className="mt-5 rounded-xl bg-red-600 px-5 py-2 text-sm font-medium text-white transition hover:bg-red-500"
            >
              تلاش دوباره
            </button>
          </div>
        ) : products.length === 0 ? (
          <div className="rounded-3xl border border-slate-800 bg-slate-900 p-10 text-center text-slate-400">
            هنوز محصول فعالی برای نمایش وجود ندارد.
          </div>
        ) : (
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {products.map((product) => <ProductCard key={product.id} product={product} />)}
          </div>
        )}
      </section>
    </div>
  );
}
