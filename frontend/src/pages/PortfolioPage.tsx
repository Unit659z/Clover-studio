import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { useSearchParams } from "react-router-dom";
import Header from "../components/Header";
import Footer from "../components/Footer";
import SearchBar from "../components/SearchBar";
import PortfolioCard from "../components/PortfolioCard";
import Pagination from "../components/Pagination";
import PortfolioFormModal from "../components/PortfolioFormModal";
import ConfirmModal from "../components/ConfirmModal";
import { useAuth } from "../context/AuthContext";
import { PortfolioItem, PaginatedResponse } from "../interfaces";

const PORTFOLIO_ITEMS_PER_PAGE = 6;

// Интерфейс для идентификатора удаления
interface PortfolioIdentifier {
  id: number;
  title: string;
}

const PortfolioPage: React.FC = () => {
  const [portfolioItems, setPortfolioItems] = useState<PortfolioItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [totalItems, setTotalItems] = useState<number>(0);

  const [searchParams, setSearchParams] = useSearchParams();

  // Получаем права из контекста
  const { canManageServices } = useAuth();

  // --- Состояния для модальных окон ---
  const [isFormModalOpen, setIsFormModalOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<PortfolioItem | null>(null);
  const [isConfirmModalOpen, setIsConfirmModalOpen] = useState(false);
  const [itemToDelete, setItemToDelete] = useState<PortfolioIdentifier | null>(
    null
  );
  const [isDeleting, setIsDeleting] = useState(false);
  const currentPage = parseInt(searchParams.get("page") || "1", 10);
  const currentSearchTerm = searchParams.get("search") || "";

  // Функция загрузки данных
  const fetchPortfolioItems = useCallback(
    async (page: number, search: string) => {
      setLoading(true);
      setError(null);

      const apiParams = new URLSearchParams();
      apiParams.set("page_size", PORTFOLIO_ITEMS_PER_PAGE.toString());
      apiParams.set("page", page.toString());
      if (search) {
        apiParams.set("search", search);
      }

      console.log(`Fetching: /studio/api/portfolios/?${apiParams.toString()}`);

      try {
        const response = await axios.get<PaginatedResponse<PortfolioItem>>(
          `/studio/api/portfolios/?${apiParams.toString()}`
        );
        setPortfolioItems(response.data.results);
        setTotalItems(response.data.count);
        setTotalPages(
          Math.ceil(response.data.count / PORTFOLIO_ITEMS_PER_PAGE)
        );
      } catch (err: any) {
        console.error("Error fetching portfolio items:", err);
        setError(err.message || "Не удалось загрузить работы портфолио.");
        setPortfolioItems([]);
        setTotalPages(1);
        setTotalItems(0);
      } finally {
        setLoading(false);
      }
    },
    []
  );

  // Загружаем данные при изменении page в searchParams
  useEffect(() => {
    const pageToFetch = parseInt(searchParams.get("page") || "1", 10);
    const searchToFetch = searchParams.get("search") || "";
    console.log(
      "PortfolioPage useEffect: Fetching page",
      pageToFetch,
      "search",
      searchToFetch
    );
    fetchPortfolioItems(Math.max(1, pageToFetch), searchToFetch);
  }, [searchParams, fetchPortfolioItems]);

  const handlePageChange = (page: number) => {
    setSearchParams(
      (prevParams) => {
        const newParams = new URLSearchParams(prevParams);
        newParams.set("page", page.toString());
        return newParams;
      },
      { replace: true }
    );
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  //Обработчик изменения поиска
  const handleSearchChange = (newSearchTerm: string) => {
    console.log(
      "PortfolioPage handleSearchChange updating URL search and page"
    );
    setSearchParams(
      (prevParams) => {
        const newParams = new URLSearchParams(prevParams);
        if (newSearchTerm.trim()) {
          newParams.set("search", newSearchTerm.trim());
        } else {
          newParams.delete("search");
        }
        newParams.set("page", "1");
        return newParams;
      },
      { replace: true }
    );
  };

  // --- Обработчики для CRUD ---
  const handleOpenAddModal = () => {
    setEditingItem(null);
    setIsFormModalOpen(true);
  };

  const handleOpenEditModal = (item: PortfolioItem) => {
    setEditingItem(item);
    setIsFormModalOpen(true);
  };

  const handleCloseFormModal = () => {
    setIsFormModalOpen(false);
    setEditingItem(null);
  };

  const handleOpenConfirmModal = (item: PortfolioItem) => {
    setItemToDelete({ id: item.pk, title: item.title });
    setIsConfirmModalOpen(true);
  };

  const handleCloseConfirmModal = () => {
    setIsConfirmModalOpen(false);
    setItemToDelete(null);
  };

  const handleDelete = async () => {
    if (!itemToDelete) return;
    setIsDeleting(true);
    try {
      await axios.delete(`/studio/api/portfolios/${itemToDelete.id}/`);
      fetchPortfolioItems(currentPage, currentSearchTerm);
      handleCloseConfirmModal();
    } catch (err: any) {
      console.error("Error deleting portfolio item:", err.response?.data);
      alert(
        `Ошибка удаления работы "${itemToDelete.title}": ${
          err.response?.data?.detail || err.message
        }`
      );
    } finally {
      setIsDeleting(false);
    }
  };

  const handleFormSubmit = async (formData: FormData, itemId?: number) => {
    const url = itemId
      ? `/studio/api/portfolios/${itemId}/`
      : "/studio/api/portfolios/";
    const method = itemId ? "patch" : "post";
    try {
      await axios({
        method: method,
        url: url,
        data: formData,
        headers: { "Content-Type": "multipart/form-data" },
      });
      fetchPortfolioItems(currentPage, currentSearchTerm);
      handleCloseFormModal();
    } catch (err) {
      console.error("Error submitting portfolio form:", err);
      throw err;
    }
  };

  return (
    <div className="bg-[#0D0C0C] text-gray-100 min-h-screen flex flex-col">
      <Header />
      <main className="flex-grow container mx-auto px-4 py-8 md:py-12">
        {/* Заголовок страницы */}
        <section className="mb-8 flex flex-col sm:flex-row justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold text-white mb-3 text-center sm:text-left">
              Портфолио
            </h1>
            <div className="w-1/5 h-0.5 bg-[#EB0000] mb-4 mx-auto sm:mx-0"></div>
            <p className="text-gray-400 max-w-3xl mx-auto md:mx-0">
              Ознакомьтесь с некоторыми из наших лучших работ. Мы гордимся
              каждым проектом и стремимся показать наш профессионализм и
              креативность.
            </p>
          </div>
          {/*Кнопка Добавить работу*/}
          {canManageServices && (
            <button
              onClick={handleOpenAddModal}
              className="flex-shrink-0 mt-4 sm:mt-0 bg-[#EB0000] text-white py-2 px-5 rounded hover:bg-[#eb0000a0] transition duration-300 text-sm font-semibold"
            >
              + Добавить работу
            </button>
          )}
        </section>

        {/*Строка поиска */}
        <section className="mb-10">
          <SearchBar
            onSearchChange={handleSearchChange}
            initialValue={currentSearchTerm}
            placeholder="Поиск работ в портфолио..."
          />
        </section>
        {/* Сетка работ портфолио */}
        <section>
          {!loading && !error && portfolioItems.length === 0 && (
            <div className="text-center text-gray-400">
              {currentSearchTerm
                ? `Работы по запросу "${currentSearchTerm}" не найдены.`
                : "В портфолио пока нет работ."}
            </div>
          )}
          {!loading && !error && portfolioItems.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 md:gap-8">
              {portfolioItems.map((item) => (
                <div key={item.pk} className="relative group">
                  <PortfolioCard
                    pk={item.pk}
                    image_url={item.image_url}
                    title={item.title}
                    description={item.description}
                  />
                  {/* Кнопки управления  */}
                  {canManageServices && (
                    <div className="absolute top-2 right-2 z-10 flex space-x-1 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                      <button
                        onClick={() => handleOpenEditModal(item)}
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
                        onClick={() => handleOpenConfirmModal(item)}
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
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Пагинация */}
        {!loading && !error && totalItems > PORTFOLIO_ITEMS_PER_PAGE && (
          <section className="mt-12">
            <Pagination
              currentPage={currentPage}
              totalPages={totalPages}
              onPageChange={handlePageChange}
            />
          </section>
        )}
      </main>
      {/* Модальные окна */}
      <PortfolioFormModal
        isOpen={isFormModalOpen}
        onClose={handleCloseFormModal}
        onSubmit={handleFormSubmit}
        initialData={editingItem}
      />
      <ConfirmModal
        isOpen={isConfirmModalOpen}
        onClose={handleCloseConfirmModal}
        onConfirm={handleDelete}
        title="Подтвердите удаление"
        message={
          <p>
            Вы уверены, что хотите удалить работу{" "}
            <strong className="text-white">"{itemToDelete?.title}"</strong>?
          </p>
        }
        confirmText="Да, удалить"
        cancelText="Отмена"
        isLoading={isDeleting}
      />
      <Footer />
    </div>
  );
};

export default PortfolioPage;
