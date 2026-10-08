import { useEffect, useState, type FormEvent, type ReactNode } from "react";
import { Link } from "react-router-dom";
import {
  createAddress,
  deleteAddress,
  getAddresses,
  setDefaultAddress,
  type Address,
  type AddressInput,
} from "../api/addresses";
import { getMyProfile, updateMyProfile, type UserProfile } from "../api/users";
import { useAuth } from "../context/AuthContext";

const EMPTY_ADDRESS: AddressInput = {
  title: "",
  recipient_name: "",
  phone: "",
  province: "",
  city: "",
  address_line: "",
  postal_code: "",
};

export default function AccountPage() {
  const { token } = useAuth();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [addresses, setAddresses] = useState<Address[]>([]);
  const [address, setAddress] = useState<AddressInput>(EMPTY_ADDRESS);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    let active = true;

    async function loadAccount() {
      if (!token) {
        setLoading(false);
        return;
      }

      try {
        const [userData, addressData] = await Promise.all([
          getMyProfile(token),
          getAddresses(token),
        ]);
        if (active) {
          setProfile(userData);
          setAddresses(addressData);
        }
      } catch (err) {
        if (active) {
          setError(err instanceof Error ? err.message : "دریافت اطلاعات حساب انجام نشد.");
        }
      } finally {
        if (active) setLoading(false);
      }
    }

    void loadAccount();
    return () => {
      active = false;
    };
  }, [token]);

  async function saveProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token || !profile) return;

    setSaving(true);
    setError("");
    setNotice("");
    try {
      const updated = await updateMyProfile(token, {
        first_name: profile.first_name.trim(),
        last_name: profile.last_name.trim(),
        phone: profile.phone?.trim() || null,
      });
      setProfile(updated);
      setNotice("اطلاعات حساب ذخیره شد.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "ذخیره اطلاعات انجام نشد.");
    } finally {
      setSaving(false);
    }
  }

  async function addAddress(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token) return;

    setSaving(true);
    setError("");
    setNotice("");
    try {
      const created = await createAddress(token, address);
      setAddresses((items) => [...items, created]);
      setAddress(EMPTY_ADDRESS);
      setNotice("نشانی ذخیره شد.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "ثبت نشانی انجام نشد.");
    } finally {
      setSaving(false);
    }
  }

  async function makeDefault(addressId: number) {
    if (!token) return;
    setError("");
    try {
      const updated = await setDefaultAddress(token, addressId);
      setAddresses((items) =>
        items.map((item) => ({ ...item, is_default: item.id === updated.id })),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "تغییر نشانی پیش‌فرض انجام نشد.");
    }
  }

  async function removeAddress(addressId: number) {
    if (!token) return;
    setError("");
    try {
      await deleteAddress(token, addressId);
      setAddresses(await getAddresses(token));
    } catch (err) {
      setError(err instanceof Error ? err.message : "حذف نشانی انجام نشد.");
    }
  }

  if (loading) return <StatusBox>در حال دریافت حساب...</StatusBox>;

  return (
    <section className="mx-auto max-w-4xl space-y-8">
      <header>
        <h1 className="text-3xl font-black text-white">حساب کاربری</h1>
        <p className="mt-2 text-slate-400">اطلاعات شخصی و نشانی‌های تحویل</p>
      </header>

      {error && <p role="alert" className="rounded-xl border border-red-900 bg-red-950/30 p-4 text-sm text-red-300">{error}</p>}
      {notice && <p role="status" className="rounded-xl border border-emerald-900 bg-emerald-950/30 p-4 text-sm text-emerald-300">{notice}</p>}

      {profile && (
        <form onSubmit={saveProfile} className="space-y-5 rounded-3xl border border-slate-800 bg-slate-900 p-6">
          <h2 className="text-xl font-bold text-white">مشخصات</h2>
          <label className="block text-sm text-slate-300">
            ایمیل
            <input disabled value={profile.email} className="mt-2 w-full rounded-xl border border-slate-800 bg-slate-950 px-4 py-3 text-slate-500" />
          </label>
          <div className="grid gap-4 sm:grid-cols-2">
            <TextField label="نام" value={profile.first_name} onChange={(value) => setProfile({ ...profile, first_name: value })} />
            <TextField label="نام خانوادگی" value={profile.last_name} onChange={(value) => setProfile({ ...profile, last_name: value })} />
          </div>
          <TextField label="تلفن" type="tel" value={profile.phone ?? ""} onChange={(value) => setProfile({ ...profile, phone: value })} />
          <button disabled={saving} className="rounded-xl bg-blue-600 px-5 py-2.5 font-medium text-white disabled:opacity-50">
            {saving ? "در حال ذخیره..." : "ذخیره مشخصات"}
          </button>
        </form>
      )}

      <section className="space-y-4 rounded-3xl border border-slate-800 bg-slate-900 p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-xl font-bold text-white">نشانی‌ها</h2>
          <Link to="/checkout" className="text-sm text-blue-400">رفتن به تسویه‌حساب</Link>
        </div>

        {addresses.length === 0 ? (
          <p className="text-sm text-slate-400">هنوز نشانی‌ای ثبت نشده است.</p>
        ) : (
          <div className="space-y-3">
            {addresses.map((item) => (
              <div key={item.id} className="flex flex-col gap-3 rounded-2xl border border-slate-800 p-4 sm:flex-row sm:items-center">
                <div className="flex-1 text-sm leading-6 text-slate-300">
                  <strong className="text-white">{item.title}</strong>
                  {item.is_default && <span className="mr-2 text-xs text-emerald-300">پیش‌فرض</span>}
                  <p>{item.recipient_name}، {item.phone}</p>
                  <p>{item.province}، {item.city}، {item.address_line}، {item.postal_code}</p>
                </div>
                <div className="flex gap-2">
                  {!item.is_default && <button type="button" onClick={() => void makeDefault(item.id)} className="rounded-lg border border-slate-700 px-3 py-2 text-xs text-slate-300">پیش‌فرض کردن</button>}
                  <button type="button" onClick={() => void removeAddress(item.id)} className="rounded-lg border border-red-900/60 px-3 py-2 text-xs text-red-300">حذف</button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      <form onSubmit={addAddress} className="space-y-4 rounded-3xl border border-slate-800 bg-slate-900 p-6">
        <h2 className="text-xl font-bold text-white">افزودن نشانی</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          <TextField label="عنوان نشانی" value={address.title} onChange={(value) => setAddress({ ...address, title: value })} />
          <TextField label="نام گیرنده" value={address.recipient_name} onChange={(value) => setAddress({ ...address, recipient_name: value })} />
          <TextField label="تلفن" type="tel" value={address.phone} onChange={(value) => setAddress({ ...address, phone: value })} />
          <TextField label="استان" value={address.province} onChange={(value) => setAddress({ ...address, province: value })} />
          <TextField label="شهر" value={address.city} onChange={(value) => setAddress({ ...address, city: value })} />
          <TextField label="کد پستی" value={address.postal_code} onChange={(value) => setAddress({ ...address, postal_code: value })} />
        </div>
        <label className="block text-sm text-slate-300">
          نشانی کامل
          <textarea required value={address.address_line} onChange={(event) => setAddress({ ...address, address_line: event.target.value })} className="mt-2 min-h-24 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none focus:border-blue-500" />
        </label>
        <button disabled={saving} className="rounded-xl bg-blue-600 px-5 py-2.5 text-sm font-medium text-white disabled:opacity-50">
          {saving ? "در حال ذخیره..." : "ثبت نشانی"}
        </button>
      </form>
    </section>
  );
}

function TextField({
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
        required={label !== "تلفن"}
        type={type}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none focus:border-blue-500"
      />
    </label>
  );
}

function StatusBox({ children }: { children: ReactNode }) {
  return <div className="flex min-h-48 items-center justify-center rounded-3xl border border-slate-800 bg-slate-900 p-8 text-slate-400">{children}</div>;
}
