import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { getCategories, type Category } from "../api/categories";
import { getProducts, type Product } from "../api/products";
import ProductCard from "../components/ProductCard";

const PAGE_SIZE = 12;
const SORT_OPTIONS = {
  newest: { sortBy: "created_at", sortOrder: "desc" },
  "price-asc": { sortBy: "price", sortOrder: "asc" },
  "price-desc": { sortBy: "price", sortOrder: "desc" },
  "name-asc": { sortBy: "name", sortOrder: "asc" },
} as const;
type SortKey = keyof typeof SORT_OPTIONS;
function readSort(value: string | null): SortKey {
  return value && Object.prototype.hasOwnProperty.call(SORT_OPTIONS, value) ? (value as SortKey) : "newest";
}

function readPositiveInteger(value: string | null, fallback: number) {
  if (!value) {
    return fallback;
  }

  const parsed = Number(value);

  return Number.isInteger(parsed) && parsed > 0 ? parsed : fallback;
}

function readCategoryId(value: string | null) {
  if (!value) {
    return undefined;
  }

  const parsed = Number(value);

  return Number.isInteger(parsed) && parsed > 0 ? parsed : undefined;
}

export default function ProductsPage() {
  const [searchParams, setSearchParams] = useSearchParams();

  const querySearch = searchParams.get("search") ?? "";
  const queryCategory = readCategoryId(searchParams.get("category"));
  const queryPage = readPositiveInteger(searchParams.get("page"), 1);
  const querySort = readSort(searchParams.get("sort"));

  const [search, setSearch] = useState(querySearch);
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [retryCount, setRetryCount] = useState(0);

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  useEffect(() => {
    setSearch(querySearch);
  }, [querySearch]);

  useEffect(() => {
    let active = true;

    async function loadCategories() {
      try {
        const result = await getCategories();

        if (active) {
          setCategories(result.filter((category) => category.is_active));
        }
      } catch {
        if (active) {
          setCategories([]);
        }
      }
    }

    void loadCategories();

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    let active = true;

    async function loadProducts() {
      setLoading(true);
      setError("");

      try {
        const result = await getProducts({
          page: queryPage,
          limit: PAGE_SIZE,
          search: querySearch,
          categoryId: queryCategory,
          isActive: true,
          ...SORT_OPTIONS[querySort],
        });

        if (active) {
          setProducts(result.items);
          setTotal(result.total);
        }
      } catch (err) {
        if (active) {
          setProducts([]);
          setTotal(0);
          setError(
            err instanceof Error
              ? err.message
              : "دریافت محصولات انجام نشد.",
          );
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void loadProducts();

    return () => {
      active = false;
    };
  }, [queryPage, querySearch, queryCategory, querySort, retryCount]);

  function updateQuery(
    nextPage: number,
    nextSearch: string,
    nextCategory: number | undefined,
    nextSort: SortKey = querySort,
  ) {
    const nextParams = new URLSearchParams();
    if (nextSearch.trim()) nextParams.set("search", nextSearch.trim());
    if (nextCategory !== undefined) nextParams.set("category", String(nextCategory));
    if (nextPage > 1) nextParams.set("page", String(nextPage));
    if (nextSort !== "newest") nextParams.set("sort", nextSort);
    setSearchParams(nextParams);
  }

  function handleSearch(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    updateQuery(1, search, queryCategory);
  }

  function handleCategoryChange(
    event: React.ChangeEvent<HTMLSelectElement>,
  ) {
    const value = event.target.value;
    const nextCategory = value ? readCategoryId(value) : undefined;

    updateQuery(1, querySearch, nextCategory);
  }

  function handleSortChange(event: React.ChangeEvent<HTMLSelectElement>) {
    updateQuery(1, querySearch, queryCategory, readSort(event.target.value));
  }

  function handlePageChange(nextPage: number) {
    if (nextPage < 1 || nextPage > totalPages || nextPage === queryPage) {
      return;
    }

    updateQuery(nextPage, querySearch, queryCategory);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function handleReset() {
    setSearch("");
    setSearchParams(new URLSearchParams());
  }

  const pageNumbers = useMemo(() => {
    const start = Math.max(1, queryPage - 2);
    const end = Math.min(totalPages, queryPage + 2);
    const pages: number[] = [];

    for (let current = start; current <= end; current += 1) {
      pages.push(current);
    }

    return pages;
  }, [queryPage, totalPages]);

  return (
    <section className="space-y-8">
      <div>
        <h1 className="text-3xl font-black text-white">محصولات</h1>
        <p className="mt-2 text-slate-400">
          محصولات فروشگاه را جست‌وجو، فیلتر و مرتب کنید.
        </p>
      </div>

      <form
        className="rounded-3xl border border-slate-800 bg-slate-900 p-5"
        onSubmit={handleSearch}
      >
        <div className="flex flex-col gap-3 lg:flex-row">
          <input
            type="search"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="جست‌وجوی محصول..."
            aria-label="جست‌وجوی محصول"
            className="min-w-0 flex-1 rounded-2xl border border-slate-800 bg-slate-950 px-5 py-3 text-white outline-none placeholder:text-slate-500 focus:border-blue-500"
          />

          <select
            value={queryCategory ?? ""}
            onChange={handleCategoryChange}
            aria-label="فیلتر دسته‌بندی"
            className="rounded-2xl border border-slate-800 bg-slate-950 px-5 py-3 text-slate-200 outline-none focus:border-blue-500"
          >
            <option value="">همه دسته‌بندی‌ها</option>
            {categories.map((category) => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </select>

          <select
            value={querySort}
            onChange={handleSortChange}
            aria-label="مرتب‌سازی محصولات"
            className="rounded-2xl border border-slate-800 bg-slate-950 px-5 py-3 text-slate-200 outline-none focus:border-blue-500"
          >
            <option value="newest">جدیدترین</option>
            <option value="price-asc">ارزان‌ترین</option>
            <option value="price-desc">گران‌ترین</option>
            <option value="name-asc">نام محصول</option>
          </select>

          <button
            type="submit"
            disabled={loading}
            className="rounded-2xl bg-blue-600 px-7 py-3 font-medium text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
          >
            جست‌وجو
          </button>

          {(querySearch || queryCategory !== undefined || querySort !== "newest") && (
            <button
              type="button"
              onClick={handleReset}
              className="rounded-2xl border border-slate-700 px-6 py-3 text-slate-300 transition hover:bg-slate-800 hover:text-white"
            >
              پاک کردن فیلترها
            </button>
          )}
        </div>
      </form>

      {!loading && !error && (
        <div className="flex items-center justify-between text-sm text-slate-400">
          <span>{total.toLocaleString("fa-IR")} محصول</span>
          {totalPages > 1 && (
            <span>
              صفحه {queryPage.toLocaleString("fa-IR")} از{" "}
              {totalPages.toLocaleString("fa-IR")}
            </span>
          )}
        </div>
      )}

      {loading ? (
        <div
          aria-live="polite"
          className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4"
        >
          {Array.from({ length: 8 }, (_, index) => (
            <div
              key={index}
              className="overflow-hidden rounded-3xl border border-slate-800 bg-slate-900"
            >
              <div className="h-48 animate-pulse bg-slate-800" />
              <div className="space-y-4 p-5">
                <div className="h-5 animate-pulse rounded bg-slate-800" />
                <div className="h-4 w-2/3 animate-pulse rounded bg-slate-800" />
                <div className="h-5 w-1/2 animate-pulse rounded bg-slate-800" />
              </div>
            </div>
          ))}
        </div>
      ) : error ? (
        <div
          role="alert"
          className="rounded-3xl border border-red-900/50 bg-red-950/30 px-6 py-12 text-center"
        >
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
        <div className="rounded-3xl border border-slate-800 bg-slate-900 px-6 py-16 text-center">
          <h2 className="text-xl font-bold text-white">محصولی پیدا نشد</h2>
          <p className="mt-2 text-slate-400">
            عبارت جست‌وجو یا دسته‌بندی را تغییر دهید.
          </p>
          <button
            type="button"
            onClick={handleReset}
            className="mt-5 rounded-xl bg-blue-600 px-5 py-2 text-sm font-medium text-white transition hover:bg-blue-500"
          >
            نمایش همه محصولات
          </button>
        </div>
      ) : (
        <>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {products.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>

          {totalPages > 1 && (
            <nav
              aria-label="صفحه‌بندی محصولات"
              className="flex flex-wrap items-center justify-center gap-2"
            >
              <button
                type="button"
                disabled={queryPage <= 1}
                onClick={() => handlePageChange(queryPage - 1)}
                className="rounded-xl border border-slate-800 px-4 py-2 text-sm text-slate-300 transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-40"
              >
                قبلی
              </button>

              {pageNumbers.map((pageNumber) => (
                <button
                  key={pageNumber}
                  type="button"
                  aria-current={pageNumber === queryPage ? "page" : undefined}
                  onClick={() => handlePageChange(pageNumber)}
                  className={`min-w-10 rounded-xl px-3 py-2 text-sm transition ${
                    pageNumber === queryPage
                      ? "bg-blue-600 text-white"
                      : "border border-slate-800 text-slate-300 hover:bg-slate-800"
                  }`}
                >
                  {pageNumber.toLocaleString("fa-IR")}
                </button>
              ))}

              <button
                type="button"
                disabled={queryPage >= totalPages}
                onClick={() => handlePageChange(queryPage + 1)}
                className="rounded-xl border border-slate-800 px-4 py-2 text-sm text-slate-300 transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-40"
              >
                بعدی
              </button>
            </nav>
          )}
        </>
      )}
    </section>
  );
}






