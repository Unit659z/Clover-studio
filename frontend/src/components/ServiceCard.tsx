import React from "react";
import { Link } from "react-router-dom";

interface ServiceCardProps {
  serviceId: number;
  imageUrl: string;
  title: string;
  description?: string;
}

const ServiceCard: React.FC<ServiceCardProps> = ({
  serviceId,
  imageUrl,
  title,
  description,
}) => {
  return (
    <div className="bg-[#181818] rounded-lg overflow-hidden shadow-lg transform transition duration-300 hover:scale-105 flex flex-col h-full">
      {" "}
      {/* Добавили flex flex-col h-full */}
      <img src={imageUrl} alt={title} className="w-full h-40 object-cover" />
      <div className="p-5 flex flex-col flex-grow">
        <h3 className="text-xl font-semibold text-white mb-2">{title}</h3>
        <div className="w-2/5 h-0.5 bg-[#EB0000] mb-3"></div>

        {/* Условный рендеринг: описание или ссылка */}
        {description ? (
          // Если описание передано (не используется на главной)
          <p className="text-gray-400 text-sm flex-grow mb-4">{description}</p>
        ) : (
          // Если описание не передано (на главной) - показываем ссылку
          <div className="mt-auto pt-2">
            <Link
              to={`/services/${serviceId}`}
              className="text-sm text-[#EB0000] hover:text-red-400 hover:underline font-medium"
            >
              Подробнее об этой услуге →
            </Link>
          </div>
        )}
      </div>
    </div>
  );
};

export default ServiceCard;
