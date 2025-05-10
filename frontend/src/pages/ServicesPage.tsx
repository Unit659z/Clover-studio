import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { useSearchParams } from "react-router-dom";
import Header from "../components/Header";
import Footer from "../components/Footer";
import SearchBar from "../components/SearchBar";
import DetailedServiceCard from "../components/DetailedServiceCard";
import Pagination from "../components/Pagination";
import ServiceFormModal from "../components/ServiceFormModal";
import { useAuth } from "../context/AuthContext";
import ConfirmModal from "../components/ConfirmModal";
import { Service, PaginatedResponse } from "../interfaces";

// --- Интерфейс для удаляемого сервиса ---
interface ServiceIdentifier {
  id: number;
  name: string;
}

const SERVICES_PER_PAGE = 4;

const ServicesPage: React.FC = () => {
  const [services, setServices] = useState<Service[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [totalServices, setTotalServices] = useState<number>(0);

  const [searchParams, setSearchParams] = useSearchParams();
  const { canManageServices } = useAuth();
  // --- Состояния для модального окна ---
  const [isFormModalOpen, setIsFormModalOpen] = useState(false);
  const [editingService, setEditingService] = useState<Service | null>(null);

  // --- Обновляем состояния для подтверждения удаления ---
  const [isConfirmModalOpen, setIsConfirmModalOpen] = useState(false);
  const [serviceToDelete, setServiceToDelete] =
    useState<ServiceIdentifier | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const currentPage = parseInt(searchParams.get("page") || "1", 10);
  const currentSearchTerm = searchParams.get("search") || "";

  // --- Функция загрузки данных ---
  const fetchServices = useCallback(async (params: URLSearchParams) => {
    setLoading(true);
    setError(null);

    const apiParams = new URLSearchParams(params);
    apiParams.set("page_size", SERVICES_PER_PAGE.toString());
    if (!apiParams.has("page")) {
      apiParams.set("page", "1");
    }

    console.log(`Fetching: /studio/api/services/?${apiParams.toString()}`);

    try {
      const response = await axios.get<PaginatedResponse<Service>>(
        `/studio/api/services/?${apiParams.toString()}`
      );
      setServices(response.data.results);
      setTotalServices(response.data.count);
      const count = response.data.count;
      setTotalPages(Math.ceil(count / SERVICES_PER_PAGE));
    } catch (err: any) {
      console.error("Error fetching services:", err);
      setError(err.message || "Не удалось загрузить услуги.");
      setServices([]);
      setTotalPages(1);
      setTotalServices(0);
    } finally {
      setLoading(false);
    }
  }, []);

  // --- Эффект для загрузки данных при изменении searchParams ---
  useEffect(() => {
    console.log(
      "SearchParams changed, triggering fetch:",
      searchParams.toString()
    );
    fetchServices(searchParams);
  }, [searchParams, fetchServices]);

  // --- Обработчики событий ---
  const handlePageChange = (page: number) => {
    console.log("handlePageChange updating URL page to:", page);
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

  const handleSearchChange = (newSearchTerm: string) => {
    console.log("handleSearchChange updating URL search and page");
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
    setEditingService(null);
    setIsFormModalOpen(true);
  };

  const handleOpenEditModal = (service: Service) => {
    setEditingService(service);
    setIsFormModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsFormModalOpen(false);
    setEditingService(null);
  };

  const handleDeleteService = (service: Service) => {
    setServiceToDelete({ id: service.pk, name: service.name });
    setIsConfirmModalOpen(true);
  };

  // --- Обработчик отмены удаления ---
  const handleCancelDelete = () => {
    setIsConfirmModalOpen(false);
    setServiceToDelete(null);
  };

  // --- Обработчик подтверждения удаления ---
  const confirmDeleteService = async () => {
    if (!serviceToDelete) return; 

    setIsDeleting(true);
    try {
      await axios.delete(`/studio/api/services/${serviceToDelete.id}/`);
      fetchServices(searchParams);
      setIsConfirmModalOpen(false);
      setServiceToDelete(null);
    } catch (err: any) {
      console.error("Error deleting service:", err.response?.data);
      alert(
        `Ошибка удаления услуги "${serviceToDelete.name}": ${
          err.response?.data?.detail || err.message
        }`
      );
    } finally {
      setIsDeleting(false);
    }
  };

  const handleFormSubmit = async (formData: FormData, serviceId?: number) => {
    const url = serviceId
      ? `/studio/api/services/${serviceId}/`
      : "/studio/api/services/";
    const method = serviceId ? "patch" : "post";

    try {
      await axios({
        method: method,
        url: url,
        data: formData,
        headers: { "Content-Type": "multipart/form-data" },
      });
      fetchServices(searchParams);
      handleCloseModal(); 
    } catch (err) {
      console.error("Error submitting service form:", err);
      throw err; 
    }
  };

  return (
    <div className="bg-[#0D0C0C] text-gray-100 min-h-screen flex flex-col">
      <Header />
      <main className="flex-grow container mx-auto px-4 py-8 md:py-12">
        {/* Заголовок и описание страницы */}
        <section className="mb-8 flex flex-col sm:flex-row justify-between items-start">
          {" "}
          <div className="w-full sm:w-auto text-center sm:text-left mb-4 sm:mb-0">
            {" "}
            <h1 className="text-3xl font-bold text-white mb-3">
              Услуги нашей студии видеомонтажа
            </h1>
            <div className="w-4/5 h-0.5 bg-[#EB0000] mb-4 mx-auto sm:mx-0"></div>
            <p className="text-gray-400 max-w-3xl mx-auto sm:mx-0">
              Мы предлагаем услуги видеомонтажа, чтобы ваши идеи превратились в
              качественные видео, которые привлекут внимание зрителей. Наша
              команда профессионалов работает с разными форматами и всегда
              использует современные технологии. Выбирая нас, вы получаете
              отличный результат, который помогает выделиться!
            </p>
          </div>
          {/* Кнопка Добавить услугу */}
          {canManageServices && (
            <button
              onClick={handleOpenAddModal}
              className="flex-shrink-0 bg-[#EB0000] text-white py-2 px-5 rounded hover:bg-[#eb0000a0] transition duration-300 text-sm font-semibold"
            >
              + Добавить услугу
            </button>
          )}
        </section>

        {/* Строка поиска */}
        <section className="mb-10">
          <SearchBar
            onSearchChange={handleSearchChange}
            initialValue={currentSearchTerm}
            placeholder="Поиск услуг..."
          />
        </section>

        {/* Сетка услуг */}
        <section>
          {loading && (
            <div className="text-center text-gray-400">Загрузка услуг...</div>
          )}
          {error && (
            <div className="text-center text-red-500">Ошибка: {error}</div>
          )}
          {!loading && !error && services.length === 0 && (
            <div className="text-center text-gray-400">
              {currentSearchTerm
                ? `Услуги по запросу "${currentSearchTerm}" не найдены.`
                : "Услуги не найдены."}
            </div>
          )}
          {!loading && !error && services.length > 0 && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 md:gap-8">
              {services.map((service) => (
                <div key={service.pk} className="relative group">
                  <DetailedServiceCard service={service} />
                  {canManageServices && (
                    <div className="absolute top-2 right-2 z-10 flex space-x-1 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                      <button
                        onClick={() => handleOpenEditModal(service)}
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
                        onClick={() => handleDeleteService(service)}
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
        {!loading && !error && totalServices > SERVICES_PER_PAGE && (
          <section className="mt-12">
            <Pagination
              currentPage={currentPage}
              totalPages={totalPages}
              onPageChange={handlePageChange}
            />
          </section>
        )}
      </main>

      {/* Модальное окно для формы */}
      <ServiceFormModal
        isOpen={isFormModalOpen}
        onClose={handleCloseModal}
        onSubmit={handleFormSubmit}
        initialData={editingService}
      />

      {/* Модальное окно подтверждения удаления */}
      <ConfirmModal
        isOpen={isConfirmModalOpen}
        onClose={handleCancelDelete}
        onConfirm={confirmDeleteService}
        title="Подтвердите удаление"
        message={
          <p>
            Вы уверены, что хотите удалить услугу{" "}
            <strong className="text-white">"{serviceToDelete?.name}"</strong>?
            Это действие необратимо.
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

export default ServicesPage;
