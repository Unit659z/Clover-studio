import React, {
  createContext,
  useState,
  useContext,
  useEffect,
  ReactNode,
  useCallback,
  useRef,
} from "react";
import axios from "axios";
import { UserProfile, Cart, CartItem } from "../interfaces";

interface Notification {
  type: "success" | "error";
  message: string;
  id: number;
}

interface AuthCredentials {
  identifier: string;
  password: string;
}

interface AuthContextType {
  isAuthenticated: boolean;
  isAuthLoading: boolean;
  currentUser: UserProfile | null;
  canManageServices: boolean;
  canManagePortfolio: boolean;
  canManageNews: boolean;
  cart: Cart | null;
  isCartLoading: boolean;
  fetchCart: () => Promise<void>; // Загрузить/обновить корзину
  addToCart: (serviceId: number, quantity?: number) => Promise<void>;
  updateCartItem: (itemId: number, quantity: number) => Promise<void>;
  removeCartItem: (itemId: number) => Promise<void>;
  clearCart: () => Promise<void>;

  login: (credentials: AuthCredentials) => Promise<void>;
  logout: () => Promise<void>;
  checkAuthStatus: () => Promise<void>;
  updateUserProfile: (
    updatedData: Partial<UserProfile> | FormData
  ) => Promise<void>;
  notifications: Notification[];
  addNotification: (type: "success" | "error", message: string) => void;
  removeNotification: (id: number) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({
  children,
}) => {
  const [currentUser, setCurrentUser] = useState<UserProfile | null>(null);
  const [isAuthLoading, setIsAuthLoading] = useState(true);
  const [cart, setCart] = useState<Cart | null>(null);
  const [isCartLoading, setIsCartLoading] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const prevUserRef = useRef<UserProfile | null>(null);
  const canManageContent =
    !!currentUser && (currentUser.is_staff || currentUser.is_executor);

  const canManageNews = !!currentUser && currentUser.is_staff;
  // --- Функции для уведомлений ---
  const addNotification = useCallback(
    (type: "success" | "error", message: string) => {
      const id = Date.now();
      setNotifications((prev) => [...prev, { id, type, message }]);
      //  удаляем через 5 секунд
      setTimeout(() => {
        removeNotification(id);
      }, 5000);
    },
    []
  );

  const removeNotification = useCallback((id: number) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  }, []);

  // --- Функция загрузки корзины ---
  const fetchCart = useCallback(async () => {
    if (isCartLoading) return; // Предотвращаем одновременные запросы
    console.log("Fetching cart...");
    setIsCartLoading(true);
    try {
      // Запрос корзины; если пользователь не аутентифицирован на бэке, вернется 403/401
      const response = await axios.get<Cart>("/studio/api/cart/");
      setCart(response.data);
      console.log("Cart fetched:", response.data);
    } catch (error: any) {
      if (error.response?.status !== 401 && error.response?.status !== 403) {
        console.error(
          "Error fetching cart:",
          error.response?.data || error.message
        );
        setCart(null); // Сбрасываем корзину при других ошибках
      } else {
        console.log(
          "Cart fetch failed (unauthenticated), setting cart to null."
        );
        setCart(null); // Сбрасываем корзину, если не авторизован
      }
    } finally {
      setIsCartLoading(false);
    }
  }, [isCartLoading]);

  // --- Проверка статуса пользователя ---
  const checkAuthStatus = useCallback(async () => {
    setIsAuthLoading(true);
    console.log("Checking auth status...");
    let fetchedUser: UserProfile | null = null;
    try {
      const response = await axios.get<UserProfile>("/studio/api/auth/status/");
      fetchedUser = response.data;
      console.log("User authenticated:", response.data);
    } catch (error: any) {
      console.log("User not authenticated:", error.response?.status);
      fetchedUser = null;
      setCart(null);
    } finally {
      setCurrentUser(fetchedUser); // Устанавливаем пользователя
      setIsAuthLoading(false);
    }
  }, []);

  useEffect(() => {
    checkAuthStatus();
  }, [checkAuthStatus]);

  // --- Эффект для загрузки корзины при ИЗМЕНЕНИИ currentUser ---
  useEffect(() => {
    // Проверяем, ИЗМЕНИЛСЯ ли пользователь
    if (currentUser && prevUserRef.current !== currentUser && !isAuthLoading) {
      console.log("currentUser state updated AND changed, fetching cart...");
      fetchCart();
    } else if (!currentUser && prevUserRef.current !== null) {
      // Пользователь стал null (логаут)
      console.log("currentUser is null, clearing cart state.");
      setCart(null);
    }

    // Обновляем предыдущее значение пользователя в ref ПОСЛЕ проверок
    prevUserRef.current = currentUser;
  }, [currentUser, isAuthLoading, fetchCart]);

  // --- Функция логина ---
  const login = async (credentials: AuthCredentials) => {
    try {
      const response = await axios.post<UserProfile>(
        "/studio/api/auth/login/",
        credentials
      );
      // useEffect вызовет fetchCart
      setCurrentUser(response.data);
      console.log("Login successful. useEffect will fetch cart.");
    } catch (error: any) {
      console.error("Login failed:", error.response?.data || error.message);
      setCurrentUser(null); // Важно сбросить пользователя при ошибке
      throw error;
    }
  };

  // --- Функции для управления корзиной ---
  const addToCart = async (serviceId: number, quantity: number = 1) => {
    setIsCartLoading(true);
    try {
      await axios.post("/studio/api/cart/items/", {
        service_id: serviceId,
        quantity,
      });
      await fetchCart();
      addNotification("success", "Услуга добавлена в корзину!");
    } catch (error: any) {
      console.error("Error adding to cart:", error.response?.data);
      const msg =
        error.response?.data?.detail ||
        error.response?.data?.non_field_errors?.join(" ") ||
        "Ошибка добавления. Попробуйте снова.";
      addNotification("error", `Ошибка добавления в корзину: ${msg}`);
    } finally {
      setIsCartLoading(false);
    }
  };

  const updateCartItem = async (itemId: number, quantity: number) => {
    if (!currentUser || quantity <= 0) return;
    console.log(`Attempting to update item ${itemId} to quantity ${quantity}`);
    const dataToSend = { quantity };
    console.log("Data being sent:", dataToSend);
    setIsCartLoading(true);
    try {
      await axios.patch(`/studio/api/cart/items/${itemId}/`, dataToSend);
      await fetchCart();
    } catch (error: any) {
      console.error("Error updating cart item:", error.response?.data);
      const msg = "Ошибка обновления корзины.";
      addNotification("error", msg);
    } finally {
      setIsCartLoading(false);
    }
  };

  const removeCartItem = async (itemId: number) => {
    setIsCartLoading(true);
    try {
      await axios.delete(`/studio/api/cart/items/${itemId}/`);
      await fetchCart();
      addNotification("success", "Товар удален из корзины.");
    } catch (error: any) {
      console.error("Error removing cart item:", error.response?.data);
      const msg = "Ошибка удаления из корзины.";
      addNotification("error", msg);
    } finally {
      setIsCartLoading(false);
    }
  };

  const clearCart = async () => {
    setIsCartLoading(true);
    try {
      await axios.delete(`/studio/api/cart/clear/`);
      setCart(null);
      addNotification("success", "Корзина очищена.");
    } catch (error: any) {
      console.error("Error clearing cart:", error.response?.data);
      const msg = "Ошибка очистки корзины.";
      addNotification("error", msg);
    } finally {
      setIsCartLoading(false);
    }
  };

  const logout = async () => {
    try {
      await axios.post("/studio/api/auth/logout/"); // добавит CSRF
      console.log("Logout successful (backend response)");
    } catch (error: any) {
      console.error(
        "Logout request failed:",
        error.response?.data || error.message
      );
      // Ошибка на бэке не должна мешать сбросу состояния на фронте
    } finally {
      //  Сбрасываем состояние ВНЕ зависимости от успеха запроса
      setCurrentUser(null);
      console.log("Frontend state cleared after logout attempt.");
    }
  };
  const updateUserProfile = async (
    updatedData: Partial<UserProfile> | FormData
  ) => {
    if (!currentUser) return;
    try {
      // Axios сам определит Content-Type, если это FormData
      const response = await axios.patch<UserProfile>(
        "/studio/api/profile/",
        updatedData
      );
      setCurrentUser(response.data);
      console.log("Profile updated:", response.data);
    } catch (error: any) {
      console.error("Profile update failed:", error.response?.data);
      throw error;
    }
  };

  const value = {
    isAuthenticated: !!currentUser,
    isAuthLoading,
    currentUser,
    canManageServices: canManageContent,
    canManagePortfolio: canManageContent,
    canManageNews,
    cart,
    isCartLoading,
    fetchCart,
    addToCart,
    updateCartItem,
    removeCartItem,
    clearCart,
    notifications,
    addNotification,
    removeNotification,
    login,
    logout,
    checkAuthStatus,
    updateUserProfile,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
