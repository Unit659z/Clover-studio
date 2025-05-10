import React from 'react';
import { Link } from 'react-router-dom'; 

interface PortfolioCardProps {
  pk: number; 
  image_url: string | null;
  title: string;
  description?: string; 
}

const DEFAULT_PORTFOLIO_IMAGE = '/images/placeholder-portfolio.png';

const PortfolioCard: React.FC<PortfolioCardProps> = ({pk, image_url, title, description }) => {
  const truncateDescription = (text: string, maxLength: number = 80): string => {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };
  return (
    <div className="bg-[#181818] rounded-lg overflow-hidden shadow-lg transform transition duration-300 hover:shadow-xl flex flex-col h-full"> {/* Добавили flex */}
      <img
        src={image_url || DEFAULT_PORTFOLIO_IMAGE}
        alt={title}
        className="w-full h-56 object-cover" 
        onError={(e) => { // Обработка ошибки загрузки
           const target = e.target as HTMLImageElement;
           target.onerror = null; // Предотвратить бесконечный цикл
           target.src = DEFAULT_PORTFOLIO_IMAGE;
        }}
        
      />
      <div className="p-5 flex flex-col flex-grow">
        <h3 className="text-xl font-semibold text-white mb-2">{title}</h3>

        {/*Условный рендеринг описания */}
        
        {description && (
             <p className="text-gray-400 text-sm mb-4 flex-grow">
                 {truncateDescription(description)}
             </p>
        )}
        <div className="w-2/5 h-0.5 bg-[#EB0000] mb-4 mx-auto sm:mx-0"></div>

         {/* Ссылка "Подробнее" */}
         <div className={`mt-auto ${description ? 'pt-2' : 'pt-5'}`}> {/* Динамический отступ сверху для ссылки */}
            <Link
                to={`/portfolio/${pk}`}
                className="text-sm text-[#EB0000] hover:text-red-400 hover:underline font-medium"
            >
                Подробнее об этой работе →
            </Link>
         </div>
      </div>
    </div>
  );
};


export default PortfolioCard;