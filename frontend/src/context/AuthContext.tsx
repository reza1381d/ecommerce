import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import {
  getCurrentUser,
  login,
  type LoginRequest,
  type UserResponse,
} from "../api/auth";

interface AuthContextValue {
  user: UserResponse | null;
  token: string | null;
  loading: boolean;
  isAuthenticated: boolean;
  loginUser: (data: LoginRequest) => Promise<UserResponse>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(
  undefined,
);

const TOKEN_KEY = "ecommerce_access_token";

function readStoredToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [token, setToken] = useState<string | null>(readStoredToken);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;

    async function restoreSession() {
      const storedToken = readStoredToken();

      if (!storedToken) {
        if (active) {
          setToken(null);
          setUser(null);
          setLoading(false);
        }
        return;
      }

      try {
        const currentUser = await getCurrentUser(storedToken);

        if (active) {
          setToken(storedToken);
          setUser(currentUser);
        }
      } catch {
        try {
          localStorage.removeItem(TOKEN_KEY);
        } catch {
          // نشست در حافظه پاک می‌شود حتی اگر localStorage در دسترس نباشد.
        }

        if (active) {
          setToken(null);
          setUser(null);
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void restoreSession();

    return () => {
      active = false;
    };
  }, []);

  async function loginUser(data: LoginRequest): Promise<UserResponse> {
    const tokenResponse = await login(data);
    const currentUser = await getCurrentUser(tokenResponse.access_token);

    try {
      localStorage.setItem(TOKEN_KEY, tokenResponse.access_token);
    } catch {
      throw new Error("ذخیره نشست در این مرورگر ممکن نیست.");
    }

    setToken(tokenResponse.access_token);
    setUser(currentUser);

    return currentUser;
  }

  function logout() {
    try {
      localStorage.removeItem(TOKEN_KEY);
    } catch {
      // نشست در حافظه در هر صورت پاک می‌شود.
    }

    setToken(null);
    setUser(null);
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        isAuthenticated: Boolean(user && token),
        loginUser,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }

  return context;
}
