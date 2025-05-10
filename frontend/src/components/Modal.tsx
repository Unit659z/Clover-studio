import React, { ReactNode, useEffect } from "react";

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: ReactNode;
}

const Modal: React.FC<ModalProps> = ({ isOpen, onClose, title, children }) => {
  useEffect(() => {
    if (isOpen) {
      // Блокируем прокрутку при открытии
      document.body.style.overflow = "hidden";
    } else {
      // Разблокируем при закрытии
      document.body.style.overflow = "unset";
    }
    return () => {
      document.body.style.overflow = "unset";
    };
  }, [isOpen]);

  // Эффект для закрытия по Esc
  useEffect(() => {
    const handleEsc = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    };
    if (isOpen) {
      window.addEventListener("keydown", handleEsc);
    }
    return () => {
      window.removeEventListener("keydown", handleEsc);
    };
  }, [isOpen, onClose]);

  if (!isOpen) {
    return null;
  }

  return (
    // Оверлей (полупрозрачный фон)
    <div
      className="fixed inset-0 bg-black bg-opacity-70 z-50 flex justify-center items-center p-4 transition-opacity duration-300"
      onClick={onClose} // Закрытие по клику на фон
      aria-labelledby="modal-title"
      role="dialog"
      aria-modal="true"
    >
      {/* Контейнер модального окна */}
      <div
        className="bg-[#181818] rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto border border-gray-700"
        onClick={(e) => e.stopPropagation()} // Предотвращаем закрытие по клику внутри окна
      >
        {/* Шапка модального окна */}
        <div className="flex justify-between items-center p-4 border-b border-gray-600 sticky top-0 bg-[#181818] z-10">
          {title && (
            <h2 id="modal-title" className="text-xl font-semibold text-white">
              {title}
            </h2>
          )}
          {/* Кнопка закрытия */}
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors"
            aria-label="Закрыть окно"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={1.5}
              stroke="currentColor"
              className="w-6 h-6"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* Содержимое модального окна */}
        <div className="p-6">{children}</div>
      </div>
    </div>
  );
};

export default Modal;
