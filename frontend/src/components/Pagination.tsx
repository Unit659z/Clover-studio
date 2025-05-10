import React from "react";

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  maxPagesToShow?: number;
}

const Pagination: React.FC<PaginationProps> = ({
  currentPage,
  totalPages,
  onPageChange,
  maxPagesToShow = 5,
}) => {
  if (totalPages <= 1) {
    return null; // Не рендерим пагинацию, если страниц 1 или меньше
  }

  const handlePageClick = (page: number) => {
    if (page >= 1 && page <= totalPages && page !== currentPage) {
      onPageChange(page);
    }
  };

  const getPageNumbers = (): (number | string)[] => {
    const pageNumbers: (number | string)[] = [];
    const halfMax = Math.floor(maxPagesToShow / 2);

    if (totalPages <= maxPagesToShow) {
      // Показываем все страницы
      for (let i = 1; i <= totalPages; i++) {
        pageNumbers.push(i);
      }
    } else {
      let startPage = Math.max(1, currentPage - halfMax);
      let endPage = Math.min(totalPages, currentPage + halfMax);

      // Корректируем начало и конец
      if (currentPage - halfMax < 1) {
        endPage = Math.min(totalPages, maxPagesToShow);
      }
      if (currentPage + halfMax > totalPages) {
        startPage = Math.max(1, totalPages - maxPagesToShow + 1);
      }

      if (startPage > 1) {
        pageNumbers.push(1);
        if (startPage > 2) {
          pageNumbers.push("...");
        }
      }

      // Добавляем основные номера страниц
      for (let i = startPage; i <= endPage; i++) {
        pageNumbers.push(i);
      }

      if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
          pageNumbers.push("...");
        }
        pageNumbers.push(totalPages);
      }
    }

    return pageNumbers;
  };

  const pageNumbersToRender = getPageNumbers();

  return (
    <nav
      aria-label="Pagination"
      className="flex justify-center items-center space-x-2 mt-8 text-sm"
    >
      {/* Кнопка "Назад" */}
      <button
        onClick={() => handlePageClick(currentPage - 1)}
        disabled={currentPage === 1}
        className="px-3 py-1 rounded bg-[#181818] border border-gray-600 text-gray-400 hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        Назад
      </button>

      {/* Номера страниц */}
      {pageNumbersToRender.map((page, index) => (
        <button
          key={`${page}-${index}`} // Уникальный ключ
          onClick={() => typeof page === "number" && handlePageClick(page)}
          disabled={page === "..."}
          className={`px-3 py-1 rounded border ${
            currentPage === page
              ? "bg-[#EB0000] border-[#EB0000] text-white font-semibold z-10" // Активная страница
              : page === "..."
              ? "border-transparent text-gray-500" // Многоточие
              : "bg-[#181818] border-gray-600 text-gray-400 hover:bg-gray-700" // Обычная страница
          } ${page === "..." ? "cursor-default" : ""}`}
        >
          {page}
        </button>
      ))}

      {/* Кнопка "Вперед" */}
      <button
        onClick={() => handlePageClick(currentPage + 1)}
        disabled={currentPage === totalPages}
        className="px-3 py-1 rounded bg-[#181818] border border-gray-600 text-gray-400 hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        Вперед
      </button>
    </nav>
  );
};

export default Pagination;
