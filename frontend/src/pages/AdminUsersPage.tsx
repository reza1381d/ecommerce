import { useEffect, useState, type FormEvent } from "react";
import {
  getAdminUsers,
  type AdminUser,
  type AdminUserSortBy,
  type SortOrder,
} from "../api/adminUsers";
import { useAuth } from "../context/AuthContext";
import { useDateFormat } from "../context/DateFormatContext";

const PAGE_SIZE = 20;
const ROLE_LABELS: Record<string, string> = {
  admin: "مدیر",
  customer: "مشتری",
};


export default function AdminUsersPage() {
  const { token } = useAuth();
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [sortBy, setSortBy] = useState<AdminUserSortBy>("created_at");
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc");
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    let active = true;
    async function loadUsers() {
      if (!token) return;
      setLoading(true);
      setError("");
      try {
        const result = await getAdminUsers(token, {
          page,
          limit: PAGE_SIZE,
          search,
          sortBy,
          sortOrder,
        });
        if (active) {
          setUsers(result.items);
          setTotal(result.total);
        }
      } catch (err) {
        if (active) {
          setUsers([]);
          setTotal(0);
          setError(err instanceof Error ? err.message : "دریافت کاربران ناموفق بود.");
        }
      } finally {
        if (active) setLoading(false);
      }
    }
    void loadUsers();
    return () => { active = false; };
  }, [token, page, search, sortBy, sortOrder, retry]);

  function submitSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPage(1);
    setSearch(searchInput.trim());
  }

  function changeSort(field: AdminUserSortBy) {
    if (field === sortBy) {
      setSortOrder((current) => current === "asc" ? "desc" : "asc");
    } else {
      setSortBy(field);
      setSortOrder(field === "created_at" || field === "id" ? "desc" : "asc");
    }
    setPage(1);
  }

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const sortLabel = sortOrder === "asc" ? "صعودی" : "نزولی";

  return (
    <section dir="rtl" className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-black text-white">مدیریت کاربران</h1>
          <p className="mt-2 text-slate-400">فهرست کاربران با جست‌وجو، مرتب‌سازی و صفحه‌بندی</p>
        </div>
        <button type="button" disabled={loading} onClick={() => setRetry((value) => value + 1)} className="rounded-xl border border-slate-700 px-4 py-2 text-sm text-slate-200 hover:bg-slate-800 disabled:opacity-50">به‌روزرسانی</button>
      </header>

      <div className="grid gap-3 rounded-2xl border border-slate-800 bg-slate-900 p-4 md:grid-cols-[1fr_auto_auto]">
        <form onSubmit={submitSearch} className="flex min-w-0 gap-2">
          <input value={searchInput} onChange={(event) => setSearchInput(event.target.value)} placeholder="جست‌وجو با ایمیل، نام، تلفن، نقش یا شناسه" aria-label="جست‌وجوی کاربران" className="min-w-0 flex-1 rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none focus:border-blue-500" />
          <button type="submit" className="rounded-xl bg-blue-600 px-4 text-sm font-medium text-white hover:bg-blue-500">جست‌وجو</button>
        </form>
        <label className="flex items-center gap-2 text-sm text-slate-400">مرتب‌سازی
          <select value={sortBy} onChange={(event) => changeSort(event.target.value as AdminUserSortBy)} className="rounded-xl border border-slate-700 bg-slate-950 px-3 py-3 text-slate-200">
            <option value="created_at">تاریخ ثبت‌نام</option>
            <option value="id">شناسه</option>
            <option value="email">ایمیل</option>
            <option value="first_name">نام</option>
            <option value="last_name">نام خانوادگی</option>
            <option value="role">نقش</option>
          </select>
        </label>
        <button type="button" onClick={() => setSortOrder((value) => value === "asc" ? "desc" : "asc")} className="rounded-xl border border-slate-700 px-4 py-3 text-sm text-slate-200">{sortLabel}</button>
      </div>

      {error && <div role="alert" className="rounded-2xl border border-red-900/50 bg-red-950/30 p-4 text-red-300"><p>{error}</p><button type="button" onClick={() => setRetry((value) => value + 1)} className="mt-2 underline">تلاش دوباره</button></div>}
      <div className="flex justify-between text-sm text-slate-400"><span>{total.toLocaleString("fa-IR")} کاربر</span><span>{loading ? "در حال بارگذاری..." : `صفحه ${page.toLocaleString("fa-IR")} از ${totalPages.toLocaleString("fa-IR")}`}</span></div>

      {loading ? (
        <div aria-live="polite" className="rounded-2xl border border-slate-800 bg-slate-900 p-10 text-center text-slate-400">در حال دریافت کاربران...</div>
      ) : users.length === 0 ? (
        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-10 text-center text-slate-400">کاربری با این مشخصات پیدا نشد.</div>
      ) : (
        <>
        <div className="space-y-3 lg:hidden">{users.map(user => <UserCard key={user.id} user={user} />)}</div>
        <div className="hidden overflow-x-auto rounded-2xl border border-slate-800 lg:block">
          <table className="w-full min-w-[850px] text-right text-sm">
            <thead className="bg-slate-900 text-slate-400"><tr><th className="p-4">شناسه</th><th className="p-4">کاربر</th><th className="p-4">تلفن</th><th className="p-4">نقش</th><th className="p-4">وضعیت</th><th className="p-4">تاریخ عضویت</th></tr></thead>
            <tbody>{users.map((user) => <UserRow key={user.id} user={user} />)}</tbody>
          </table>
        </div>
        </>
      )}

      {totalPages > 1 && <nav aria-label="صفحه‌بندی کاربران" className="flex items-center justify-center gap-3"><button type="button" disabled={page <= 1 || loading} onClick={() => setPage((value) => value - 1)} className="rounded-xl border border-slate-700 px-4 py-2 text-sm disabled:opacity-40">قبلی</button><span className="text-sm text-slate-400">صفحه {page.toLocaleString("fa-IR")} از {totalPages.toLocaleString("fa-IR")}</span><button type="button" disabled={page >= totalPages || loading} onClick={() => setPage((value) => value + 1)} className="rounded-xl border border-slate-700 px-4 py-2 text-sm disabled:opacity-40">بعدی</button></nav>}
    </section>
  );
}

function UserCard({ user }: { user: AdminUser }) {
  const { formatDate } = useDateFormat();
  return <article className="space-y-3 rounded-2xl border border-slate-800 bg-slate-900 p-4 text-sm"><header className="flex items-start justify-between gap-3"><div className="min-w-0"><p className="font-semibold text-white">{user.first_name} {user.last_name}</p><p className="mt-1 break-all text-xs text-slate-400">{user.email}</p></div><span className="shrink-0 rounded-full bg-slate-800 px-2.5 py-1 text-xs text-slate-300">#{user.id.toLocaleString("fa-IR")}</span></header><dl className="grid grid-cols-2 gap-3 border-t border-slate-800 pt-3 text-xs"><div><dt className="text-slate-500">تلفن</dt><dd className="mt-1 text-slate-300">{user.phone || "—"}</dd></div><div><dt className="text-slate-500">نقش</dt><dd className="mt-1 text-slate-300">{ROLE_LABELS[user.role] ?? user.role}</dd></div><div><dt className="text-slate-500">وضعیت</dt><dd className={`mt-1 ${user.is_active ? "text-emerald-300" : "text-red-300"}`}>{user.is_active ? "فعال" : "غیرفعال"}</dd></div><div><dt className="text-slate-500">تاریخ عضویت</dt><dd className="mt-1 text-slate-300">{formatDate(user.created_at, { dateStyle: "medium" })}</dd></div></dl></article>;
}

function UserRow({ user }: { user: AdminUser }) {
  const { formatDate } = useDateFormat();
  return <tr className="border-t border-slate-800 text-slate-300"><td className="p-4">#{user.id.toLocaleString("fa-IR")}</td><td className="p-4"><p className="font-medium text-white">{user.first_name} {user.last_name}</p><p className="mt-1 text-xs text-slate-500">{user.email}</p></td><td className="p-4">{user.phone || "—"}</td><td className="p-4">{ROLE_LABELS[user.role] ?? user.role}</td><td className="p-4"><span className={user.is_active ? "text-emerald-300" : "text-red-300"}>{user.is_active ? "فعال" : "غیرفعال"}</span></td><td className="p-4">{formatDate(user.created_at, { dateStyle: "medium", timeStyle: "short" })}</td></tr>;
}
