import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import Header from "../components/Header";
import Footer from "../components/Footer";
import { CartItem } from "../interfaces";

// Компонент для строки товара в корзине
const CartItemRow: React.FC<{
  item: CartItem;
  onUpdate: (itemId: number, quantity: number) => void;
  onRemove: (itemId: number) => void;
  isUpdating: boolean; // Флаг общей загрузки корзины
}> = ({ item, onUpdate, onRemove, isUpdating }) => {
  const [quantity, setQuantity] = useState(item.quantity);
  const [debounceTimeout, setDebounceTimeout] = useState<NodeJS.Timeout | null>(
    null
  );

  const handleQuantityChange = (newQuantity: number) => {
    const updatedQuantity = Math.max(1, newQuantity);
    setQuantity(updatedQuantity);

    if (debounceTimeout) {
      clearTimeout(debounceTimeout);
    }

    const timer = setTimeout(() => {
      // Вызываем обновление только если количество действительно изменилось
      if (updatedQuantity !== item.quantity) {
        onUpdate(item.pk, updatedQuantity);
      }
    }, 750);
    setDebounceTimeout(timer);
  };

  useEffect(() => {
    return () => {
      if (debounceTimeout) clearTimeout(debounceTimeout);
    };
  }, [debounceTimeout]);

  const handleIncrement = () => handleQuantityChange(quantity + 1);
  const handleDecrement = () => handleQuantityChange(quantity - 1);

  return (
    <div className="flex items-center justify-between py-4 border-b border-gray-700 gap-4 flex-wrap sm:flex-nowrap">
      {/* Товар */}
      <div className="flex items-center gap-4 flex-grow min-w-[200px]">
        <img
          src={item.service?.photo_url || "/images/placeholder-service.png"}
          alt={item.service?.name || "Услуга"}
          className="w-16 h-16 object-cover rounded"
          onError={(e) => {
            const target = e.target as HTMLImageElement;
            target.onerror = null;
            target.src = "/images/placeholder-service.png";
          }}
        />
        <div>
          {/* Добавляем проверку */}
          {item.service ? (
            <Link
              to={`/services/${item.service.pk}`}
              className="font-medium text-white hover:text-[#EB0000]"
            >
              {item.service.name}
            </Link>
          ) : (
            <span className="font-medium text-gray-500 italic">
              Услуга удалена
            </span>
          )}
          <p className="text-sm text-gray-400">
            {item.service
              ? `${parseFloat(item.service.price).toLocaleString(
                  "ru-RU"
                )} ₽ / шт.`
              : "---"}
          </p>
        </div>
      </div>

      {/* Количество */}
      <div className="flex items-center border border-gray-600 rounded flex-shrink-0">
        <button
          onClick={handleDecrement}
          disabled={isUpdating || quantity <= 1}
          className="px-2 py-1 text-gray-400 hover:text-white disabled:opacity-50"
        >
          -
        </button>
        <input
          type="number"
          min="1"
          value={quantity}
          onChange={(e) =>
            handleQuantityChange(parseInt(e.target.value, 10) || 1)
          }
          disabled={isUpdating}
          className="w-12 text-center bg-transparent border-none focus:outline-none focus:ring-0 text-white"
        />
        <button
          onClick={handleIncrement}
          disabled={isUpdating}
          className="px-2 py-1 text-gray-400 hover:text-white disabled:opacity-50"
        >
          +
        </button>
      </div>

      {/* Стоимость */}
      <div className="text-right flex-shrink-0 min-w-[100px]">
        <p className="font-medium text-white">
          {parseFloat(item.total_cost).toLocaleString("ru-RU")} ₽
        </p>
      </div>

      {/* Удалить */}
      <div className="flex-shrink-0">
        <button
          onClick={() => onRemove(item.pk)}
          disabled={isUpdating}
          title="Удалить"
          className="text-gray-500 hover:text-red-500 disabled:opacity-50"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={1.5}
            stroke="currentColor"
            className="w-5 h-5"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0"
            />
          </svg>
        </button>
      </div>
    </div>
  );
};

const CartPage: React.FC = () => {
  const { cart, isCartLoading, updateCartItem, removeCartItem, clearCart } =
    useAuth();

  return (
    <div className="bg-[#0D0C0C] text-gray-100 min-h-screen flex flex-col">
      <Header />
      <main className="flex-grow container mx-auto px-4 py-8 md:py-12">
        <h1 className="text-3xl font-bold text-white mb-8">Ваша корзина</h1>

        {isCartLoading && (
          <p className="text-center text-gray-400">Загрузка корзины...</p>
        )}

        {!isCartLoading && (!cart || cart.items.length === 0) && (
          <div className="text-center text-gray-400 bg-[#181818] p-8 rounded-lg">
            <p className="text-xl mb-4">Ваша корзина пуста.</p>
            <Link
              to="/services"
              className="text-[#EB0000] hover:underline font-medium"
            >
              Перейти к выбору услуг
            </Link>
          </div>
        )}

        {!isCartLoading && cart && cart.items.length > 0 && (
          <div className="bg-[#181818] p-6 rounded-lg shadow-xl">
            {/* Список товаров */}
            <div className="mb-6">
              {cart.items.map((item) => (
                <CartItemRow
                  key={item.pk}
                  item={item}
                  onUpdate={updateCartItem}
                  onRemove={removeCartItem}
                  isUpdating={isCartLoading} // Блокируем кнопки во время любого обновления корзины
                />
              ))}
            </div>

            {/* Итоговая информация и кнопки */}
            <div className="flex flex-col sm:flex-row justify-between items-center border-t border-gray-600 pt-6 gap-4">
              <button
                onClick={clearCart}
                disabled={isCartLoading}
                className="text-sm text-gray-400 hover:text-red-500 disabled:opacity-50"
              >
                Очистить корзину
              </button>
              <div className="text-right">
                <p className="text-lg">
                  Итого ({cart.total_items_count} шт.):{" "}
                  <span className="font-bold text-xl text-white">
                    {parseFloat(cart.total_cost).toLocaleString("ru-RU")} ₽
                  </span>
                </p>
                <button
                  disabled={isCartLoading}
                  className="mt-4 bg-[#EB0000] text-white py-2 px-6 rounded hover:bg-[#eb0000a0] transition duration-300 disabled:opacity-50"
                >
                  Перейти к оформлению
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
      <Footer />
    </div>
  );
};

export default CartPage;
