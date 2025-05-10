import React from "react";
import { Service } from "../interfaces";
import { Link } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useAuth } from "../context/AuthContext";

// Placeholder, если у услуги нет фото
const placeholderServiceImage = "/images/placeholder-service.png";

interface DetailedServiceCardProps {
  service: Service;
}

// форматирование цены
const formatPrice = (price: string | number): string => {
  const num = Number(price);
  if (isNaN(num)) {
    return String(price);
  }
  return num.toLocaleString("ru-RU", { minimumFractionDigits: 0 });
};

const DetailedServiceCard: React.FC<{ service: Service }> = ({ service }) => {
  const { addToCart, isCartLoading } = useAuth();

  const handleAddToCart = () => {
    addToCart(service.pk); // Вызываем добавление
  };

  return (
    <div className="bg-[#181818] rounded-lg overflow-hidden shadow-lg flex flex-col h-full">
      <img
        src={service.photo_url || placeholderServiceImage}
        alt={service.name}
        className="w-full h-48 object-cover"
        onError={(e) => {}}
      />
      <div className="p-5 flex flex-col flex-grow">
        <div className="flex justify-between items-start mb-2">
          <h3 className="text-xl font-semibold text-white">{service.name}</h3>
          <span className="text-lg font-semibold text-white whitespace-nowrap ml-4">
            от {formatPrice(service.price)}₽
          </span>
        </div>
        <div className="w-1/4 h-0.5 bg-[#EB0000] mb-4"></div>

        {/* Блок описания */}
        <div className="text-gray-400 text-sm mb-4 overflow-hidden line-clamp-5">
          {" "}
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              ul: ({ node, ...props }) => (
                <ul className="space-y-1" {...props} />
              ),
              li: ({ node, ...props }) => (
                <li className="flex items-start" {...props}>
                  <span className="text-[#EB0000] mr-2 mt-1 flex-shrink-0">
                    ●
                  </span>
                  <span>{props.children}</span>
                </li>
              ),
            }}
          >
            {service.description || "Описание не доступно."}
          </ReactMarkdown>
        </div>

        {/* Ссылка Подробнее */}
        <div className="mb-4">
          <Link
            to={`/services/${service.pk}`}
            className="text-xs text-[#EB0000] hover:text-red-400 hover:underline font-medium"
          >
            Подробнее об этой услуге →
          </Link>
        </div>

        {/* Кнопка Заказать */}
        <div className="mt-auto pt-2">
          <button
            onClick={handleAddToCart}
            disabled={isCartLoading}
            className="w-full bg-[#EB0000] text-white py-2 px-4 rounded hover:bg-[#eb0000a0] transition duration-300 text-sm disabled:opacity-50"
          >
            В корзину
          </button>
        </div>
      </div>
    </div>
  );
};

export default DetailedServiceCard;
