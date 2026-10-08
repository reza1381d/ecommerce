import { useState, type FormEvent } from "react";
import {
  Link,
  Navigate,
  useNavigate,
} from "react-router-dom";
import { register } from "../api/auth";
import { useAuth } from "../context/AuthContext";

export default function RegisterPage() {
  const navigate = useNavigate();
  const { loading: sessionLoading, isAuthenticated } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [phone, setPhone] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (sessionLoading) {
    return (
      <section
        aria-live="polite"
        className="flex min-h-[60vh] items-center justify-center text-slate-400"
      >
        در حال بررسی وضعیت حساب...
      </section>
    );
  }

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSubmitting(true);

    try {
      const normalizedEmail = email.trim();

      await register({
        email: normalizedEmail,
        password,
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        phone: phone.trim() || null,
      });

      navigate("/login", {
        replace: true,
        state: {
          registered: true,
          email: normalizedEmail,
        },
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "ثبت‌نام انجام نشد.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="flex min-h-[70vh] items-center justify-center">
      <div className="w-full max-w-lg rounded-3xl border border-slate-800 bg-slate-900 p-8 shadow-xl">
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold text-white">ایجاد حساب</h1>
          <p className="mt-3 text-slate-400">
            اطلاعات حساب کاربری خود را وارد کنید.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="grid gap-5 sm:grid-cols-2">
            <div>
              <label
                htmlFor="register-first-name"
                className="mb-2 block text-sm font-medium text-slate-300"
              >
                نام
              </label>
              <input
                id="register-first-name"
                name="first_name"
                type="text"
                value={firstName}
                onChange={(event) => setFirstName(event.target.value)}
                required
                autoComplete="given-name"
                className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none transition focus:border-blue-500"
              />
            </div>

            <div>
              <label
                htmlFor="register-last-name"
                className="mb-2 block text-sm font-medium text-slate-300"
              >
                نام خانوادگی
              </label>
              <input
                id="register-last-name"
                name="last_name"
                type="text"
                value={lastName}
                onChange={(event) => setLastName(event.target.value)}
                required
                autoComplete="family-name"
                className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none transition focus:border-blue-500"
              />
            </div>
          </div>

          <div>
            <label
              htmlFor="register-email"
              className="mb-2 block text-sm font-medium text-slate-300"
            >
              ایمیل
            </label>
            <input
              id="register-email"
              name="email"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
              autoComplete="email"
              className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none transition focus:border-blue-500"
              placeholder="example@email.com"
            />
          </div>

          <div>
            <label
              htmlFor="register-phone"
              className="mb-2 block text-sm font-medium text-slate-300"
            >
              شماره تلفن{" "}
              <span className="text-slate-500">(اختیاری)</span>
            </label>
            <input
              id="register-phone"
              name="phone"
              type="tel"
              value={phone}
              onChange={(event) => setPhone(event.target.value)}
              autoComplete="tel"
              className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none transition focus:border-blue-500"
            />
          </div>

          <div>
            <label
              htmlFor="register-password"
              className="mb-2 block text-sm font-medium text-slate-300"
            >
              رمز عبور
            </label>
            <input
              id="register-password"
              name="password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
              autoComplete="new-password"
              className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none transition focus:border-blue-500"
            />
          </div>

          {error && (
            <div
              role="alert"
              className="rounded-2xl border border-red-900/50 bg-red-950/30 px-4 py-3 text-sm text-red-300"
            >
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-2xl bg-blue-600 px-5 py-3 font-semibold text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {submitting ? "در حال ثبت‌نام..." : "ثبت‌نام"}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-slate-400">
          قبلاً حساب ساخته‌اید؟{" "}
          <Link
            to="/login"
            className="font-medium text-blue-400 transition hover:text-blue-300"
          >
            وارد شوید
          </Link>
        </p>
      </div>
    </section>
  );
}