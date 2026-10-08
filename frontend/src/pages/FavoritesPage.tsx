import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getProduct, type Product } from "../api/products";
import ProductCard from "../components/ProductCard";
import { useFavorites } from "../context/FavoritesContext";

export default function FavoritesPage() {
  const { favoriteIds } = useFavorites();
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    async function loadFavorites() {
      if (favoriteIds.length === 0) {
        setProducts([]);
        setLoading(false);
        setError("");
        return;
      }
      setLoading(true);
      setError("");
      const results = await Promise.allSettled(favoriteIds.map((id) => getProduct(id)));
      if (active) {
        setProducts(results.flatMap((result) => result.status === "fulfilled" ? [result.value] : []));
        if (results.every((result) => result.status === "rejected")) {
          setError("محصولات علاقه‌مندی دریافت نشدند. دوباره تلاش کن.");
        }
        setLoading(false);
      }
    }
    void loadFavorites();
    return () => { active = false; };
  }, [favoriteIds]);

  return (
    <section className="space-y-8">
      <header>
        <h1 className="text-3xl font-black text-white">علاقه‌مندی‌های من</h1>
        <p className="mt-2 text-slate-400">محصولاتی که برای بعد ذخیره کرده‌ای.</p>
      </header>
      {error && <p role="alert" className="rounded-2xl border border-red-900/50 bg-red-950/30 p-4 text-sm text-red-300">{error}</p>}
      {loading ? (
        <div aria-live="polite" className="rounded-3xl border border-slate-800 bg-slate-900 p-10 text-center text-slate-400">در حال دریافت علاقه‌مندی‌ها...</div>
      ) : products.length ? (
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">{products.map((product) => <ProductCard key={product.id} product={product} />)}</div>
      ) : !error ? (
        <div className="rounded-3xl border border-dashed border-slate-700 bg-slate-900/50 p-10 text-center">
          <p className="text-slate-300">هنوز محصولی ذخیره نکرده‌ای.</p>
          <Link to="/products" className="mt-4 inline-flex rounded-xl bg-blue-600 px-4 py-2 text-sm font-semibold text-white">دیدن محصولات</Link>
        </div>
      ) : null}
    </section>
  );
}
