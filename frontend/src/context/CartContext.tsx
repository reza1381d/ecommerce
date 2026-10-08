import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import {
  addCartItem,
  getCart,
  removeCartItem,
  updateCartItem,
  type CartResponse,
} from "../api/cart";
import { useAuth } from "./AuthContext";

interface CartContextValue {
  cart: CartResponse | null;
  itemCount: number;
  loading: boolean;
  error: string;
  refresh: () => Promise<void>;
  addItem: (productId: number, quantity?: number) => Promise<void>;
  updateItem: (itemId: number, quantity: number) => Promise<void>;
  removeItem: (itemId: number) => Promise<void>;
}

const CartContext = createContext<CartContextValue | undefined>(undefined);

export function CartProvider({ children }: { children: ReactNode }) {
  const { token, loading: authLoading, isAuthenticated } = useAuth();
  const [cart, setCart] = useState<CartResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    if (!token || !isAuthenticated) {
      setCart(null);
      setError("");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const result = await getCart(token);
      setCart(result);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "دریافت سبد خرید انجام نشد.",
      );
      throw err;
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated, token]);

  useEffect(() => {
    if (authLoading) {
      return;
    }

    if (!isAuthenticated || !token) {
      setCart(null);
      setError("");
      setLoading(false);
      return;
    }

    void refresh().catch(() => undefined);
  }, [authLoading, isAuthenticated, refresh, token]);

  const addItem = useCallback(
    async (productId: number, quantity = 1) => {
      if (!token || !isAuthenticated) {
        throw new Error("برای افزودن محصول ابتدا وارد حساب خود شوید.");
      }

      setError("");
      await addCartItem(token, {
        product_id: productId,
        quantity,
      });
      await refresh();
    },
    [isAuthenticated, refresh, token],
  );

  const updateItem = useCallback(
    async (itemId: number, quantity: number) => {
      if (!token) {
        throw new Error("برای تغییر سبد خرید وارد حساب خود شوید.");
      }

      setError("");
      await updateCartItem(token, itemId, { quantity });
      await refresh();
    },
    [refresh, token],
  );

  const removeItem = useCallback(
    async (itemId: number) => {
      if (!token) {
        throw new Error("برای تغییر سبد خرید وارد حساب خود شوید.");
      }

      setError("");
      await removeCartItem(token, itemId);
      await refresh();
    },
    [refresh, token],
  );

  const itemCount = useMemo(
    () => cart?.items.reduce((sum, item) => sum + item.quantity, 0) ?? 0,
    [cart],
  );

  const value = useMemo(
    () => ({
      cart,
      itemCount,
      loading,
      error,
      refresh,
      addItem,
      updateItem,
      removeItem,
    }),
    [addItem, cart, error, itemCount, loading, refresh, removeItem, updateItem],
  );

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}

export function useCart() {
  const context = useContext(CartContext);

  if (!context) {
    throw new Error("useCart must be used inside CartProvider");
  }

  return context;
}
