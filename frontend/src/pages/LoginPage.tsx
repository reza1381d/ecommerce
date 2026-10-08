import { useState, type FormEvent } from "react";
import {
  Link,
  Navigate,
  useLocation,
  useNavigate,
} from "react-router-dom";
import { useAuth } from "../context/AuthContext";

interface LoginLocationState {
  from?: {
    pathname?: string;
  };
  registered?: boolean;
  email?: string;
}

function getPostLoginPath(state: unknown, role?: string) {
  if (state && typeof state === "object") {
    const returnPath = (state as LoginLocationState).from?.pathname;

    if (
      typeof returnPath === "string" &&
      returnPath.startsWith("/") &&
      !returnPath.startsWith("//") &&
      returnPath !== "/"
    ) {
      return returnPath;
    }
  }

  return role === "admin" ? "/admin" : "/";
}

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const {
    loginUser,
    loading: sessionLoading,
    isAuthenticated,
    user,
  } = useAuth();

  const locationState = location.state as LoginLocationState | null;
  const [email, setEmail] = useState(locationState?.email ?? "");
  const [password, setPassword] = useState("");
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
    return (
      <Navigate
        to={getPostLoginPath(locationState, user?.role)}
        replace
      />
    );
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSubmitting(true);

    try {
      const loggedInUser = await loginUser({
        email: email.trim(),
        password,
      });

      navigate(getPostLoginPath(locationState, loggedInUser.role), {
        replace: true,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "ورود انجام نشد.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="flex min-h-[70vh] items-center justify-center">
      <div className="w-full max-w-md rounded-3xl border border-slate-800 bg-slate-900 p-8 shadow-xl">
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold text-white">ورود به حساب</h1>
          <p className="mt-3 text-slate-400">
            برای ادامه وارد حساب کاربری خود شوید.
          </p>
        </div>

        {locationState?.registered && (
          <div
            role="status"
            className="mb-5 rounded-2xl border border-emerald-900/50 bg-emerald-950/30 px-4 py-3 text-sm text-emerald-300"
          >
            ثبت‌نام انجام شد. اکنون با حساب خود وارد شوید.
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label
              htmlFor="login-email"
              className="mb-2 block text-sm font-medium text-slate-300"
            >
              ایمیل
            </label>
            <input
              id="login-email"
              name="email"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
              autoComplete="email"
              autoFocus
              className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none transition focus:border-blue-500"
              placeholder="example@email.com"
            />
          </div>

          <div>
            <label
              htmlFor="login-password"
              className="mb-2 block text-sm font-medium text-slate-300"
            >
              رمز عبور
            </label>
            <input
              id="login-password"
              name="password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
              autoComplete="current-password"
              className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none transition focus:border-blue-500"
              placeholder="رمز عبور"
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
            {submitting ? "در حال ورود..." : "ورود"}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-slate-400">
          حساب کاربری ندارید؟{" "}
          <Link
            to="/register"
            className="font-medium text-blue-400 transition hover:text-blue-300"
          >
            ثبت‌نام کنید
          </Link>
        </p>
      </div>
    </section>
  );
}
