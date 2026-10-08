import { BrowserRouter, Navigate, Outlet, Route, Routes, useLocation } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { CartProvider } from "./context/CartContext";
import { FavoritesProvider } from "./context/FavoritesContext";
import AdminLayout from "./layouts/AdminLayout";
import StoreLayout from "./layouts/StoreLayout";
import AdminDashboard from "./pages/AdminDashboard";
import AdminProductsPage from "./pages/AdminProductsPage";
import AdminCategoriesPage from "./pages/AdminCategoriesPage";
import AdminCouponsPage from "./pages/AdminCouponsPage";
import AdminOrdersPage from "./pages/AdminOrdersPage";
import AdminUsersPage from "./pages/AdminUsersPage";
import AdminPaymentsPage from "./pages/AdminPaymentsPage";
import AdminSettingsPage from "./pages/AdminSettingsPage";
import { StoreSettingsProvider } from "./context/StoreSettingsContext";
import { DateFormatProvider } from "./context/DateFormatContext";
import AccountPage from "./pages/AccountPage";
import CartPage from "./pages/CartPage";
import CategoryProductsPage from "./pages/CategoryProductsPage";
import CheckoutPage from "./pages/CheckoutPage";
import HomePage from "./pages/HomePage";
import LoginPage from "./pages/LoginPage";
import OrdersPage from "./pages/OrdersPage";
import PaymentsPage from "./pages/PaymentsPage";
import ProductDetailPage from "./pages/ProductDetailPage";
import ProductsPage from "./pages/ProductsPage";
import RegisterPage from "./pages/RegisterPage";
import FavoritesPage from "./pages/FavoritesPage";

function RequireAuth() {
  const { loading, isAuthenticated } = useAuth();
  const location = useLocation();
  if (loading) return <GateMessage>در حال بررسی ورود...</GateMessage>;
  return isAuthenticated ? <Outlet /> : <Navigate to="/login" state={{ from: location }} replace />;
}
function RequireAdmin() {
  const { user, loading, isAuthenticated } = useAuth();
  const location = useLocation();
  if (loading) return <GateMessage>در حال بررسی دسترسی...</GateMessage>;
  if (!isAuthenticated) return <Navigate to="/login" state={{ from: location }} replace />;
  return user?.role === "admin" ? <Outlet /> : <Navigate to="/" replace />;
}
function GateMessage({ children }: { children: string }) {
  return <div dir="rtl" aria-live="polite" className="flex min-h-screen items-center justify-center text-slate-300">{children}</div>;
}
function NotFoundPage() {
  return <section className="py-24 text-center"><h1 className="text-3xl font-black text-white">این صفحه پیدا نشد</h1><a className="mt-5 inline-block text-blue-400" href="/">بازگشت به فروشگاه</a></section>;
}
export default function App() {
  return <DateFormatProvider><AuthProvider><CartProvider><FavoritesProvider><StoreSettingsProvider><BrowserRouter><Routes>
    <Route element={<StoreLayout />}>
      <Route path="/" element={<HomePage />} /><Route path="/products" element={<ProductsPage />} />
      <Route path="/products/:productId" element={<ProductDetailPage />} /><Route path="/category/:category" element={<CategoryProductsPage />} />
      <Route path="/favorites" element={<FavoritesPage />} />
      <Route path="/login" element={<LoginPage />} /><Route path="/register" element={<RegisterPage />} />
      <Route element={<RequireAuth />}><Route path="/cart" element={<CartPage />} /><Route path="/checkout" element={<CheckoutPage />} /><Route path="/account" element={<AccountPage />} /><Route path="/orders" element={<OrdersPage />} /><Route path="/payments" element={<PaymentsPage />} /></Route>
      <Route path="*" element={<NotFoundPage />} />
    </Route>
    <Route element={<RequireAdmin />}><Route element={<AdminLayout />}>
      <Route path="/admin" element={<AdminDashboard />} /><Route path="/admin/products" element={<AdminProductsPage />} /><Route path="/admin/categories" element={<AdminCategoriesPage />} /><Route path="/admin/coupons" element={<AdminCouponsPage />} />
      <Route path="/admin/orders" element={<AdminOrdersPage />} /><Route path="/admin/users" element={<AdminUsersPage />} /><Route path="/admin/payments" element={<AdminPaymentsPage />} /><Route path="/admin/settings" element={<AdminSettingsPage />} />
    </Route></Route>
  </Routes></BrowserRouter></StoreSettingsProvider></FavoritesProvider></CartProvider></AuthProvider></DateFormatProvider>;
}





