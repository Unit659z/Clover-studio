import React from "react";
import { Order } from "../interfaces";

// Импортируем функцию форматирования цены
const formatPrice = (price: string | number): string => {
  const num = Number(price);
  if (isNaN(num)) {
    return String(price);
  }
  return num.toLocaleString("ru-RU", {
    minimumFractionDigits: 0,
    style: "currency",
    currency: "RUB",
    currencyDisplay: "symbol",
  });
};

// Функция форматирования даты
const formatDate = (dateString: string | null): string => {
  if (!dateString) return "---";
  try {
    return new Date(dateString).toLocaleString("ru-RU", {
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch (e) {
    return "Некорректная дата";
  }
};

interface OrderDetailContentProps {
  order: Order;
}

const OrderDetailContent: React.FC<OrderDetailContentProps> = ({ order }) => {
  return (
    <div className="space-y-4 text-sm">
      {/* Основная информация */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-2">
        <div>
          <span className="text-gray-400 block">Номер заказа:</span>
          <span className="font-medium text-white">#{order.pk}</span>
        </div>
        <div>
          <span className="text-gray-400 block">Статус:</span>
          <span
            className={`font-medium px-2 py-0.5 rounded text-xs ${
              order.status?.status_name === "completed"
                ? "bg-green-600 text-white"
                : order.status?.status_name === "cancelled"
                ? "bg-red-700 text-white"
                : order.status?.status_name === "processing"
                ? "bg-orange-600 text-white"
                : "bg-blue-600 text-white" // new
            }`}
          >
            {order.status?.display_name || "Неизвестен"}
          </span>
        </div>
      </div>

      <hr className="border-gray-600" />

      {/* Услуга */}
      <div>
        <span className="text-gray-400 block">Услуга:</span>
        <span className="font-medium text-white">
          {order.service?.name || (
            <span className="text-gray-500 italic">Услуга удалена</span>
          )}
        </span>
        {order.service?.price && (
          <span className="text-gray-300 ml-2">
            ({formatPrice(order.service.price)})
          </span>
        )}
      </div>

      <hr className="border-gray-600" />

      {/* Клиент и Исполнитель */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-2">
        <div>
          <span className="text-gray-400 block">Клиент:</span>
          <span className="font-medium text-white">
            {order.client?.full_name || order.client?.username || (
              <span className="text-gray-500 italic">Клиент удален</span>
            )}
          </span>
        </div>
        <div>
          <span className="text-gray-400 block">Исполнитель:</span>
          <span className="font-medium text-white">
            {order.executor?.user?.full_name ||
              order.executor?.user?.username || (
                <span className="text-gray-500 italic">
                  Не назначен или удален
                </span>
              )}
          </span>
        </div>
      </div>

      <hr className="border-gray-600" />

      {/* Даты */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-x-4 gap-y-2">
        <div>
          <span className="text-gray-400 block">Дата создания:</span>
          <span className="font-medium text-white">
            {formatDate(order.created_at)}
          </span>
        </div>
        <div>
          <span className="text-gray-400 block">План. время:</span>
          <span className="font-medium text-white">
            {formatDate(order.scheduled_at)}
          </span>
        </div>
        <div>
          <span className="text-gray-400 block">Дата завершения:</span>
          <span className="font-medium text-white">
            {formatDate(order.completed_at)}
          </span>
        </div>
      </div>
    </div>
  );
};

export default OrderDetailContent;
