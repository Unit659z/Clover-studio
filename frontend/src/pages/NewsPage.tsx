import React, { useState, useEffect, useCallback, useRef } from "react";
import axios from "axios";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import Header from "../components/Header";
import Footer from "../components/Footer";
import NewsFormModal from "../components/NewsFormModal";
import ConfirmModal from "../components/ConfirmModal";
import { useAuth } from "../context/AuthContext";
import { News, PaginatedResponse } from "../interfaces";

// --- Компонент для одной новости ---
const NewsItemDisplay: React.FC<{
  newsItem: News;
  onEdit: (item: News) => void;
  onDelete: (item: News) => void;
  canManage: boolean;
}> = ({ newsItem, onEdit, onDelete, canManage }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const contentRef = useRef<HTMLDivElement>(null);
  const [needsExpansionButton, setNeedsExpansionButton] = useState(false);

  const MAX_COLLAPSED_HEIGHT_PX = 200;

  useEffect(() => {
    // Сбрасываем состояние при смене новости или контента
    setIsExpanded(false);
    setNeedsExpansionButton(false);

    if (contentRef.current) {
      const scrollHeight = contentRef.current.scrollHeight;

      if (scrollHeight > MAX_COLLAPSED_HEIGHT_PX) {
        setNeedsExpansionButton(true);
      } else {
        setNeedsExpansionButton(false);
      }
    }
    // Пересчитываем только когда меняется контент или сама новость
  }, [newsItem.content, newsItem.pk]);

  const formatDate = (dateString: string | null): string => {
    if (!dateString) return "Дата не указана";
    try {
      return new Date(dateString).toLocaleDateString("ru-RU", {
        year: "numeric",
        month: "long",
        day: "numeric",
      });
    } catch (e) {
      return "Некорректная дата";
    }
  };

  return (
    <section
      id={`news-${newsItem.pk}`}
      className="snap-start snap-always w-full flex items-center justify-center py-4 md:py-6 border-b border-gray-800 min-h-[40vh]"
    >
      <article className="bg-[#181818] rounded-lg shadow-xl p-4 md:p-6 w-full max-w-6xl relative">
        {" "}
        {canManage && (
          <div className="absolute top-4 right-4 z-20 flex space-x-1">
            <button
              onClick={() => onEdit(newsItem)}
              title="Редактировать"
              className="p-1.5 bg-blue-600 hover:bg-blue-700 rounded text-white"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth={1.5}
                stroke="currentColor"
                className="w-4 h-4"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L10.582 16.07a4.5 4.5 0 0 1-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 0 1 1.13-1.897l8.932-8.931Zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0 1 15.75 21H5.25A2.25 2.25 0 0 1 3 18.75V8.25A2.25 2.25 0 0 1 5.25 6H10"
                />
              </svg>
            </button>
            <button
              onClick={() => onDelete(newsItem)}
              title="Удалить"
              className="p-1.5 bg-red-600 hover:bg-red-700 rounded text-white"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth={1.5}
                stroke="currentColor"
                className="w-4 h-4"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0"
                />
              </svg>
            </button>
          </div>
        )}
        <h1 className="text-xl md:text-2xl font-bold text-white mb-2">
          {newsItem.title}
        </h1>
        <div className="flex items-center text-xs text-gray-500 mb-3">
          <span>{formatDate(newsItem.published_at)}</span>
          {newsItem.author && (
            <>
              <span className="mx-2">|</span>
              <span>
                Автор: {newsItem.author.full_name || newsItem.author.username}
              </span>
            </>
          )}
        </div>
        <div
          ref={contentRef}
          className={`prose prose-invert prose-sm md:prose-base max-w-none text-gray-300 overflow-hidden transition-all duration-500 ease-in-out`}
          style={{
            maxHeight:
              !isExpanded && needsExpansionButton
                ? `${MAX_COLLAPSED_HEIGHT_PX}px`
                : "none",
            ...(!isExpanded &&
              needsExpansionButton && {
                WebkitMaskImage:
                  "linear-gradient(to bottom, black 70%, transparent 100%)",
                maskImage:
                  "linear-gradient(to bottom, black 70%, transparent 100%)",
              }),
          }}
        >
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {newsItem.content}
          </ReactMarkdown>
        </div>
        {/* Кнопка "Читать полностью / Свернуть" */}
        {needsExpansionButton && (
          <button
            onClick={() => {
              setIsExpanded(!isExpanded);
              if (contentRef.current) {
                if (!isExpanded) {
                  contentRef.current.style.maxHeight = "none";
                } else {
                  contentRef.current.style.maxHeight = `${MAX_COLLAPSED_HEIGHT_PX}px`;
                }
              }
            }}
            className="mt-4 text-sm text-[#EB0000] hover:underline focus:outline-none"
          >
            {isExpanded ? "Свернуть" : "Читать полностью..."}
          </button>
        )}
        {newsItem.pdf_file_url && (
          <div className="mt-4 pt-4 border-t border-gray-700">
            <a
              href={newsItem.pdf_file_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center text-sm text-[#EB0000] hover:text-red-400 hover:underline font-medium"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 20 20"
                fill="currentColor"
                className="w-5 h-5 mr-2"
              >
                <path
                  fillRule="evenodd"
                  d="M15.621 4.379a3 3 0 0 0-4.242 0l-7 7a3 3 0 0 0 4.241 4.243h.001l.497-.5a.75.75 0 0 1 1.064 1.057l-.498.501-.002.002a4.5 4.5 0 0 1-6.364-6.364l7-7a4.5 4.5 0 0 1 6.368 6.36l-3.455 3.553A2.625 2.625 0 1 1 9.52 9.52l3.45-3.451a.75.75 0 1 1 1.061 1.06l-3.45 3.451a1.125 1.125 0 0 0 1.587 1.595l3.454-3.553a3 3 0 0 0 0-4.242Z"
                  clipRule="evenodd"
                />
              </svg>
              Скачать PDF
            </a>
          </div>
        )}
      </article>
    </section>
  );
};

const NewsPage: React.FC = () => {
  const [newsItems, setNewsItems] = useState<News[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [hasNextPage, setHasNextPage] = useState<boolean>(false);
  const [isLoadingMore, setIsLoadingMore] = useState<boolean>(false);
  const { canManageNews } = useAuth();

  const scrollContainerRef = useRef<HTMLDivElement>(null);

  // --- Состояния для модальных окон ---
  const [isFormModalOpen, setIsFormModalOpen] = useState(false);
  const [editingNews, setEditingNews] = useState<News | null>(null);
  const [isConfirmModalOpen, setIsConfirmModalOpen] = useState(false);
  const [newsToDelete, setNewsToDelete] = useState<{
    id: number;
    title: string;
  } | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const fetchNews = useCallback(
    async (page: number, append: boolean = false) => {
      if (append) setIsLoadingMore(true);
      else setLoading(true);
      setError(null);

      try {
        const response = await axios.get<PaginatedResponse<News>>(
          `/studio/api/news/?page=${page}`
        );
        if (append) {
          setNewsItems((prevItems) => [...prevItems, ...response.data.results]);
        } else {
          setNewsItems(response.data.results);
        }
        setHasNextPage(response.data.next !== null);
      } catch (err: any) {
        console.error("Error fetching news:", err);
        setError(err.message || "Не удалось загрузить новости.");
      } finally {
        if (append) setIsLoadingMore(false);
        else setLoading(false);
      }
    },
    []
  );

  useEffect(() => {
    fetchNews(1);
  }, [fetchNews]);

  const loadMoreNews = () => {
    if (hasNextPage && !isLoadingMore) {
      const nextPage = currentPage + 1;
      fetchNews(nextPage, true);
      setCurrentPage(nextPage);
    }
  };

  // --- Обработчики CRUD для новостей ---
  const handleOpenAddModal = () => {
    setEditingNews(null);
    setIsFormModalOpen(true);
  };
  const handleOpenEditModal = (item: News) => {
    setEditingNews(item);
    setIsFormModalOpen(true);
  };
  const handleCloseFormModal = () => {
    setIsFormModalOpen(false);
    setEditingNews(null);
  };

  const handleOpenConfirmDelete = (item: News) => {
    setNewsToDelete({ id: item.pk, title: item.title });
    setIsConfirmModalOpen(true);
  };
  const handleCloseConfirmDelete = () => {
    setIsConfirmModalOpen(false);
    setNewsToDelete(null);
  };

  const confirmDeleteNews = async () => {
    if (!newsToDelete) return;
    setIsDeleting(true);
    try {
      await axios.delete(`/studio/api/news/${newsToDelete.id}/`);
      setNewsItems((prev) => prev.filter((n) => n.pk !== newsToDelete.id));
      handleCloseConfirmDelete();
    } catch (err: any) {
      console.error("Delete news error", err);
    } finally {
      setIsDeleting(false);
    }
  };

  const handleFormSubmit = async (formData: FormData, newsId?: number) => {
    const url = newsId ? `/studio/api/news/${newsId}/` : "/studio/api/news/";
    const method = newsId ? "patch" : "post";
    try {
      await axios({
        method,
        url,
        data: formData,
        headers: { "Content-Type": "multipart/form-data" },
      });
      fetchNews(1, false); // Перезагружаем с первой страницы
      setCurrentPage(1);
      handleCloseFormModal();
    } catch (err) {
      throw err;
    }
  };

  return (
    <div className="bg-[#0D0C0C] text-gray-100 min-h-screen flex flex-col">
      <Header />
      {canManageNews && (
        <div className="container mx-auto px-4 pt-4 md:pt-6 text-right">
          <button
            onClick={handleOpenAddModal}
            className="bg-[#EB0000] text-white py-2 px-5 rounded hover:bg-[#eb0000a0] transition duration-300 text-sm font-semibold"
          >
            + Добавить новость
          </button>
        </div>
      )}

      <div
        ref={scrollContainerRef}
        className="flex-grow overflow-y-auto snap-y snap-mandatory scroll-smooth"
      >
        {loading && newsItems.length === 0 && (
          <div className="h-full flex justify-center items-center text-gray-400">
            Загрузка новостей...
          </div>
        )}
        {error && (
          <div className="h-full flex justify-center items-center text-red-500">
            Ошибка: {error}
          </div>
        )}
        {!loading && newsItems.length === 0 && !error && (
          <div className="h-full flex justify-center items-center text-gray-400">
            Новостей пока нет.
          </div>
        )}

        {newsItems.map((newsItem) => (
          <NewsItemDisplay
            key={newsItem.pk}
            newsItem={newsItem}
            onEdit={handleOpenEditModal}
            onDelete={handleOpenConfirmDelete}
            canManage={canManageNews}
          />
        ))}

        {hasNextPage && !isLoadingMore && (
          <div className="snap-start snap-always w-full flex items-center justify-center py-4 md:py-6 border-b border-gray-800 min-h-[70vh]">
            <button
              onClick={loadMoreNews}
              className="bg-[#EB0000] text-white py-2 px-6 rounded hover:bg-[#eb0000a0] transition duration-300"
            >
              Загрузить еще новости
            </button>
          </div>
        )}
        {isLoadingMore && (
          <div className="snap-start snap-always w-full flex items-center justify-center py-4 md:py-6 border-b border-gray-800 min-h-[20vh] text-gray-400">
            Загрузка...
          </div>
        )}
        {!hasNextPage && newsItems.length > 0 && !loading && (
          <div className="snap-start snap-always w-full flex items-center justify-center py-4 md:py-6 border-b border-gray-800 min-h-[20vh] text-gray-500">
            Больше новостей нет.
          </div>
        )}
      </div>
      {/* Модальные окна */}
      <NewsFormModal
        isOpen={isFormModalOpen}
        onClose={handleCloseFormModal}
        onSubmit={handleFormSubmit}
        initialData={editingNews}
      />
      <ConfirmModal
        isOpen={isConfirmModalOpen}
        onClose={handleCloseConfirmDelete}
        onConfirm={confirmDeleteNews}
        title="Подтвердите удаление новости"
        message={
          <p>
            Удалить новость{" "}
            <strong className="text-white">"{newsToDelete?.title}"</strong>?
          </p>
        }
        isLoading={isDeleting}
      />
      <Footer />
    </div>
  );
};

export default NewsPage;
