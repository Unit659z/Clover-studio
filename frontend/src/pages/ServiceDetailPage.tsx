import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom'; 
import axios from 'axios';
import ReactMarkdown from 'react-markdown'; 
import remarkGfm from 'remark-gfm'; 
import remarkBreaks from 'remark-breaks'; 
import Header from '../components/Header';
import Footer from '../components/Footer';
import { Service } from '../interfaces';
import { useAuth } from '../context/AuthContext'; 

const placeholderServiceImage = '/images/placeholder-service.png';

// Функция форматирования цены 
const formatPrice = (price: string | number): string => {
    const num = Number(price);
    if (isNaN(num)) {
        return String(price);
    }
    return num.toLocaleString('ru-RU', { minimumFractionDigits: 0, style: 'currency', currency: 'RUB', currencyDisplay: 'symbol' }); // Формат валюты
}



const ServiceDetailPage: React.FC = () => {
  const { pk } = useParams<{ pk: string }>();
  const [service, setService] = useState<Service | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const { addToCart, isCartLoading } = useAuth();

  const fetchServiceDetail = useCallback(async () => {
    if (!pk) { setError("Не указан ID услуги."); setLoading(false); return; }
    setLoading(true); setError(null);
    try {
      const response = await axios.get<Service>(`/studio/api/services/${pk}/`);
      setService(response.data);
    } catch (err: any) {
      console.error("Error fetching service detail:", err);
      if (err.response?.status === 404) { setError("Услуга не найдена."); }
      else { setError(err.message || "Не удалось загрузить данные услуги."); }
      setService(null);
    } finally { setLoading(false); }
  }, [pk]);

  useEffect(() => {
    fetchServiceDetail();
  }, [fetchServiceDetail]);

  const handleAddToCart = () => {
    if (service) {
        addToCart(service.pk);
    }
};


  return (
    <div className="bg-[#0D0C0C] text-gray-100 min-h-screen flex flex-col">
      <Header />
      <main className="flex-grow container mx-auto px-4 py-8 md:py-12">
        {loading && <div className="text-center text-gray-400 py-10">Загрузка услуги...</div>}
        {error && <div className="text-center text-red-500 py-10">Ошибка: {error}</div>}

        {service && !loading && !error && (
          <article> 
            {/* Верхняя часть: Изображение и Заголовок/Цена */}
            <div className="relative bg-[#181818] rounded-lg shadow-xl overflow-hidden mb-8 md:mb-12 border border-gray-800">
                 <div className="absolute inset-0 bg-gradient-to-t from-[#181818] via-[#181818]/70 to-transparent z-10"></div>
                <img
                  src={service.photo_url || placeholderServiceImage}
                  alt={service.name}
                  className="w-full h-[40vh] md:h-[55vh] object-cover" 
                  onError={(e) => { }}
                />
                {/* Текстовый блок поверх градиента */}
                <div className="absolute bottom-0 left-0 right-0 p-6 md:p-10 z-20">
                     <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-white mb-3 drop-shadow-md">{service.name}</h1>
                     <div className="w-1/5 h-1 bg-[#EB0000] mb-4"></div>
                     <p className="text-xl sm:text-2xl font-semibold text-white drop-shadow-sm">
                         Стоимость: {formatPrice(service.price)}
                     </p>
                      <p className="text-gray-300 text-sm mt-1">
                         Примерная длительность: {service.duration_hours} ч.
                     </p>
                </div>
            </div>

            {/* Основной контент: Описание и кнопка */}
            <div className="bg-[#181818] rounded-lg shadow-xl p-6 md:p-8 border border-gray-800">
                 <h2 className="text-2xl font-semibold text-white mb-4">Подробное описание</h2>
                 <div className="prose prose-invert prose-sm md:prose-base max-w-none text-gray-300">
                     <ReactMarkdown remarkPlugins={[remarkGfm, remarkBreaks]}>
                         {service.description || 'Подробное описание отсутствует.'}
                     </ReactMarkdown>
                 </div>

                 {/* Кнопка заказа */}
                 <div className="mt-8 pt-6 border-t border-gray-700 text-center">
                 <button
                     onClick={handleAddToCart}
                     disabled={isCartLoading || !service}
                     className="bg-[#EB0000] text-white py-2.5 px-8 rounded text-lg font-semibold hover:bg-[#eb0000a0] transition duration-300 disabled:opacity-50"
                 >
                     Добавить в корзину
                 </button>
                      <p className="mt-4 text-sm text-gray-500">
                          <Link to="/services" className="hover:text-[#EB0000] underline">Вернуться к списку услуг</Link>
                      </p>
                 </div>
            </div>
          </article>
        )}
      </main>
      <Footer />
    </div>
  );
};

export default ServiceDetailPage;