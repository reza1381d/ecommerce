import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { createProduct, deleteProduct, getProducts, productImageSrc, removeProductImage, updateProduct, uploadProductImage, type Product, type ProductInput } from "../api/products";
import { getCategories, type Category } from "../api/categories";
import { useAuth } from "../context/AuthContext";
import { useStoreSettings } from "../context/StoreSettingsContext";
import { currencyInputValue, currencyStorageValue, currencyLabel, formatMoney } from "../utils/currency";

const blank: ProductInput = { name: "", description: "", price: 0, stock: 0, category_id: null };
const MAX_IMAGE_SIZE = 5 * 1024 * 1024;

export default function AdminProductsPage() {
  const { token } = useAuth();
  const { settings } = useStoreSettings();
  const [items, setItems] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [form, setForm] = useState<ProductInput>(blank);
  const [editing, setEditing] = useState<Product | null>(null);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [previewUrl, setPreviewUrl] = useState<string | undefined>();
  const activeCategories = useMemo(() => categories.filter(c => c.is_active), [categories]);

  async function load() {
    setLoading(true); setError("");
    try { const [products, categoryList] = await Promise.all([getProducts({ page: 1, limit: 100, search: search.trim() }), getCategories()]); setItems(products.items); setCategories(categoryList); }
    catch (e) { setError(e instanceof Error ? e.message : "بارگذاری اطلاعات ناموفق بود."); }
    finally { setLoading(false); }
  }
  useEffect(() => { void load(); }, []);
  useEffect(() => { if (!imageFile) { setPreviewUrl(undefined); return; } const url = URL.createObjectURL(imageFile); setPreviewUrl(url); return () => URL.revokeObjectURL(url); }, [imageFile]);

  function clearForm() { setEditing(null); setForm(blank); setImageFile(null); }
  async function submit(event: React.FormEvent) {
    event.preventDefault(); if (!token) return;
    if (imageFile && (!imageFile.type.match(/^image\/(jpeg|png|webp)$/) || imageFile.size > MAX_IMAGE_SIZE)) { setError("تصویر باید JPG، PNG یا WebP و حداکثر ۵ مگابایت باشد."); return; }
    setBusy(true); setError(""); setNotice("");
    const canonicalPrice = Number.isInteger(Number(form.price)) ? Number(form.price) : null;
    if (canonicalPrice === null) { setError(settings.currencyUnit === "rial" ? "برای ذخیرهٔ صحیح تومان، قیمت ریالی باید مضرب ۱۰ باشد." : "قیمت باید عدد صحیح باشد."); setBusy(false); return; }
    const data = { ...form, price: canonicalPrice, stock: Number(form.stock), category_id: form.category_id ? Number(form.category_id) : null };
    try {
      const saved = editing ? await updateProduct(token, editing.id, data) : await createProduct(token, data);
      if (imageFile) {
        try { await uploadProductImage(token, saved.id, imageFile); }
        catch (e) { setEditing(saved); setError(`محصول ذخیره شد اما بارگذاری تصویر ناموفق بود: ${e instanceof Error ? e.message : "خطای ناشناخته"} دوباره تلاش کن.`); await load(); return; }
      }
      clearForm(); setNotice("محصول ذخیره شد."); await load();
    } catch (e) { setError(e instanceof Error ? e.message : "ذخیره محصول ناموفق بود."); }
    finally { setBusy(false); }
  }
  function edit(product: Product) { setEditing(product); setForm({ name: product.name, description: product.description ?? "", price: product.price, stock: product.stock, category_id: product.category_id }); setImageFile(null); window.scrollTo({ top: 0, behavior: "smooth" }); }
  async function toggle(product: Product) { if (!token) return; try { await updateProduct(token, product.id, { is_active: !product.is_active }); await load(); } catch (e) { setError(e instanceof Error ? e.message : "تغییر وضعیت ناموفق بود."); } }
  async function remove(product: Product) { if (!token || !window.confirm(`محصول «${product.name}» حذف شود؟`)) return; try { await deleteProduct(token, product.id); await load(); } catch (e) { setError(e instanceof Error ? e.message : "حذف محصول ناموفق بود."); } }
  async function removeImage() { if (!token || !editing) return; setBusy(true); setError(""); try { const updated = await removeProductImage(token, editing.id); setEditing(updated); setItems(current => current.map(item => item.id === updated.id ? updated : item)); setNotice("تصویر محصول حذف شد."); } catch (e) { setError(e instanceof Error ? e.message : "حذف تصویر ناموفق بود."); } finally { setBusy(false); } }

  return <section dir="rtl" className="space-y-6">
    <header><h1 className="text-3xl font-black text-white">مدیریت محصولات</h1><p className="mt-2 text-slate-400">افزودن، ویرایش، فعال‌سازی و حذف محصول و تصویر آن.</p></header>
    <form onSubmit={submit} className="grid gap-4 rounded-3xl border border-slate-800 bg-slate-900 p-5 sm:grid-cols-2">
      <h2 className="text-lg font-bold text-white sm:col-span-2">{editing ? "ویرایش محصول" : "محصول جدید"}</h2>
      <input required value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder="نام محصول" className="rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white" />
      <select value={form.category_id ?? ""} onChange={e => setForm({ ...form, category_id: e.target.value ? Number(e.target.value) : null })} className="rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white"><option value="">بدون دسته‌بندی</option>{activeCategories.map(category => <option key={category.id} value={category.id}>{category.name}</option>)}</select>
      <textarea value={form.description ?? ""} onChange={e => setForm({ ...form, description: e.target.value })} placeholder="توضیحات" className="min-h-24 rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white sm:col-span-2" />
      <label className="text-sm text-slate-400">قیمت ({currencyLabel(settings.currencyUnit)})<input required min="0" step={settings.currencyUnit === "rial" ? "10" : "1"} type="number" value={currencyInputValue(form.price, settings.currencyUnit)} onChange={e => setForm({ ...form, price: currencyStorageValue(Number(e.target.value), settings.currencyUnit) ?? Number(e.target.value) / (settings.currencyUnit === "rial" ? 10 : 1) })} className="mt-2 block w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white" /></label>
      <label className="text-sm text-slate-400">موجودی<input required min="0" type="number" value={form.stock} onChange={e => setForm({ ...form, stock: Number(e.target.value) })} className="mt-2 block w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white" /></label>
      <div className="space-y-3 sm:col-span-2"><label className="block text-sm text-slate-400">تصویر محصول (JPG، PNG یا WebP، حداکثر ۵ مگابایت)<input type="file" accept="image/jpeg,image/png,image/webp" onChange={e => setImageFile(e.target.files?.[0] ?? null)} className="mt-2 block w-full rounded-xl border border-slate-700 bg-slate-950 p-3 text-white file:ml-3 file:rounded-lg file:border-0 file:bg-slate-700 file:px-3 file:py-2" /></label>
        {(previewUrl || editing?.image_url) && <div className="flex items-center gap-4"><img src={previewUrl ?? productImageSrc(editing?.image_url)} alt="پیش‌نمایش تصویر محصول" className="h-28 w-28 rounded-xl border border-slate-700 object-cover" />{editing?.image_url && !imageFile && <button type="button" disabled={busy} onClick={() => void removeImage()} className="text-sm text-red-400">حذف تصویر فعلی</button>}</div>}</div>
      <div className="flex gap-3 sm:col-span-2"><button disabled={busy} className="rounded-xl bg-blue-600 px-5 py-3 font-medium text-white disabled:opacity-50">{busy ? "در حال ذخیره..." : editing ? "ذخیره ویرایش" : "افزودن محصول"}</button>{editing && <button type="button" onClick={clearForm} className="rounded-xl border border-slate-700 px-5 text-slate-300">لغو</button>}</div>
    </form>
    {error && <p role="alert" className="rounded-xl bg-red-950/40 p-4 text-red-300">{error}</p>}{notice && <p aria-live="polite" className="text-emerald-400">{notice}</p>}
    <div className="flex gap-3"><input value={search} onChange={e => setSearch(e.target.value)} onKeyDown={e => e.key === "Enter" && void load()} placeholder="جست‌وجوی محصول" className="min-w-0 flex-1 rounded-xl border border-slate-800 bg-slate-900 px-4 py-3 text-white" /><button type="button" onClick={() => void load()} className="rounded-xl border border-slate-700 px-5">جست‌وجو</button></div>
    {loading ? <p className="p-8 text-center text-slate-400">در حال بارگذاری...</p> : <div className="overflow-x-auto rounded-2xl border border-slate-800"><table className="w-full min-w-[700px] text-right text-sm"><thead className="bg-slate-900 text-slate-400"><tr>{["تصویر", "محصول", "قیمت", "موجودی", "وضعیت", "عملیات"].map(label => <th key={label} className="p-4">{label}</th>)}</tr></thead><tbody>{items.map(product => <tr key={product.id} className="border-t border-slate-800"><td className="p-3">{product.image_url ? <img src={productImageSrc(product.image_url)} alt={product.name} className="h-12 w-12 rounded-lg object-cover" /> : <span className="text-slate-500">—</span>}</td><td className="p-4 font-medium text-white">{product.name}</td><td className="p-4">{formatMoney(product.price)}</td><td className="p-4">{product.available_stock.toLocaleString("fa-IR")}</td><td className="p-4">{product.is_active ? "فعال" : "غیرفعال"}</td><td className="space-x-3 space-x-reverse p-4"><button onClick={() => edit(product)} className="text-blue-400">ویرایش</button><button onClick={() => void toggle(product)} className="text-amber-300">{product.is_active ? "غیرفعال‌کردن" : "فعال‌کردن"}</button><button onClick={() => void remove(product)} className="text-red-400">حذف</button><Link to={`/products/${product.id}`} className="text-slate-400">نمایش</Link></td></tr>)}</tbody></table>{items.length === 0 && <p className="p-8 text-center text-slate-400">محصولی پیدا نشد.</p>}</div>}
  </section>;
}
