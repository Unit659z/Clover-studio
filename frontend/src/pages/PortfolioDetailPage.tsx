import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import Header from '../components/Header';
import Footer from '../components/Footer';
import { PortfolioItem } from '../interfaces'; 

const placeholderPortfolioImage = '/images/placeholder-portfolio.png';

const PortfolioDetailPage: React.FC = () => {
  const { pk } = useParams<{ pk: string }>();
  const [item, setItem] = useState<PortfolioItem | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPortfolioDetail = useCallback(async () => {
    if (!pk) { setError("Не указан ID работы."); setLoading(false); return; }
    setLoading(true); setError(null);
    try {
      // Используем эндпоинт детализации портфолио
      const response = await axios.get<PortfolioItem>(`/studio/api/portfolios/${pk}/`);
      setItem(response.data);
    } catch (err: any) {
      console.error("Error fetching portfolio detail:", err);
      if (err.response?.status === 404) { setError("Работа не найдена."); }
      else { setError(err.message || "Не удалось загрузить данные работы."); }
      setItem(null);
    } finally { setLoading(false); }
  }, [pk]);

  useEffect(() => {
    fetchPortfolioDetail();
  }, [fetchPortfolioDetail]);

  return (
    <div className="bg-[#0D0C0C] text-gray-100 min-h-screen flex flex-col">
      <Header />
      <main className="flex-grow container mx-auto px-4 py-8 md:py-12">
        {loading && <div className="text-center text-gray-400 py-10">Загрузка работы...</div>}
        {error && <div className="text-center text-red-500 py-10">Ошибка: {error}</div>}

        {item && !loading && !error && (
          <article>
             {/* Заголовок/Исполнитель  */}
             <div className="relative bg-[#181818] rounded-lg shadow-xl overflow-hidden mb-8 md:mb-12 border border-gray-800">
                 <div className="absolute inset-0 bg-gradient-to-t from-[#181818] via-[#181818]/70 to-transparent z-10"></div>
                 <img
                    src={item.image_url || placeholderPortfolioImage}
                    alt={item.title}
                    className="w-full h-[40vh] md:h-[60vh] object-cover"
                    onError={(e) => {
                        const target = e.target as HTMLImageElement;
                        target.onerror = null;
                        target.src = placeholderPortfolioImage;
                    }}
                 />
                 {/* Текстовый блок поверх градиента */}
                <div className="absolute bottom-0 left-0 right-0 p-6 md:p-10 z-20">
                     <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-white mb-3 drop-shadow-md">{item.title}</h1>
                     <div className="w-1/5 h-1 bg-[#EB0000] mb-4"></div>
                      <p className="text-gray-300 text-sm mt-1">
                          Исполнитель: {' '}
                          <span className="font-semibold">
                              {item.executor?.user?.full_name || item.executor?.user?.username || 'Не указан'}
                          </span>
                          {item.executor?.specialization && (
                               <span className="text-gray-400"> ({item.executor.specialization})</span>
                          )}
                      </p>
                </div>
             </div>

             {/* Основной контент */}
              <div className="bg-[#181818] rounded-lg shadow-xl p-6 md:p-8 border border-gray-800">
                 <h2 className="text-2xl font-semibold text-white mb-4">Подробное описание</h2>
                 <div className="prose prose-invert prose-sm md:prose-base max-w-none text-gray-300">
                     <ReactMarkdown remarkPlugins={[remarkGfm]}>
                         {item.description || 'Описание отсутствует.'}
                     </ReactMarkdown>
                 </div>

                 {/* Ссылка на видео (если есть) */}
                 {item.video_link && (
                    <div className="mt-8 pt-6 border-t border-gray-700"> 
                         <h3 className="text-xl font-semibold text-white mb-3">Видео/Проект</h3>
                         <a
                           href={item.video_link}
                           target="_blank"
                           rel="noopener noreferrer"
                           className="text-[#EB0000] hover:text-red-400 hover:underline break-all text-lg" 
                         >
                           {item.video_link}
                         </a>
                    </div>
                 )}

                 {/* Ссылка назад */}
                  <div className="mt-8 pt-6 border-t border-gray-700">
                       <Link to="/portfolio" className="text-sm text-gray-400 hover:text-[#EB0000] underline">
                           ← Вернуться к списку работ
                       </Link>
                  </div>
              </div>
          </article>
        )}
      </main>
      <Footer />
    </div>
  );
};

export default PortfolioDetailPage;