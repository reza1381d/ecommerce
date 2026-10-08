import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getCategories } from "../api/categories";
import { getProducts, type Product } from "../api/products";
import ProductCard from "../components/ProductCard";

export default function CategoryProductsPage() {
  const { category } = useParams();
  const categoryId = Number(category);
  const [categoryName, setCategoryName] = useState("");
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    async function loadCategoryPage() {
      if (!Number.isInteger(categoryId) || categoryId <= 0) {
        setError("شناسه دسته‌بندی معتبر نیست.");
        setLoading(false);
        return;
      }

      setLoading(true);
      setError("");

      try {
        const [categories, result] = await Promise.all([
          getCategories(),
          getProducts({
            page: 1,
            limit: 100,
            categoryId,
            isActive: true,
          }),
        ]);

        if (!active) return;

        const selected = categories.find(
          (item) => item.id === categoryId && item.is_active,
        );

        if (!selected) {
          setError("دسته‌بندی فعال پیدا نشد.");
          setProducts([]);
          return;
        }

        setCategoryName(selected.name);
        setProducts(result.items);
      } catch (err) {
        if (active) {
          setError(err instanceof Error ? err.message : "دریافت محصولات انجام نشد.");
        }
      } finally {
        if (active) setLoading(false);
      }
    }

    void loadCategoryPage();
    return () => {
      active = false;
    };
  }, [categoryId]);

  return (
    <section className="space-y-8">
      <div className="flex items-end justify-between gap-4">
        <div>
          <Link to="/products" className="text-sm text-blue-400 hover:text-blue-300">
            همه محصولات
          </Link>
          <h1 className="mt-3 text-3xl font-black text-white">
            {categoryName || "دسته‌بندی"}
          </h1>
        </div>
      </div>

      {loading ? (
        <StatusBox>در حال دریافت محصولات...</StatusBox>
      ) : error ? (
        <StatusBox>
          <p role="alert">{error}</p>
        </StatusBox>
      ) : products.length === 0 ? (
        <StatusBox>در این دسته‌بندی محصول فعالی وجود ندارد.</StatusBox>
      ) : (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {products.map((product) => (
            <ProductCard key={product.id} product={product} />
          ))}
        </div>
      )}
    </section>
  );
}

function StatusBox({ children }: { children: React.ReactNode }) {
  return (
    <div className="rounded-3xl border border-slate-800 bg-slate-900 p-10 text-center text-slate-400">
      {children}
    </div>
  );
}
