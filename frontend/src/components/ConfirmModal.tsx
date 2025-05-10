import React, { ReactNode, useEffect } from 'react';
import Modal from './Modal'; // переиспользовать базовый Modal

interface ConfirmModalProps {
  isOpen: boolean;
  onClose: () => void; // Вызывается при отмене или закрытии
  onConfirm: () => void; // Вызывается при подтверждении
  title?: string;
  message: ReactNode; 
  confirmText?: string;
  cancelText?: string;
  isLoading?: boolean; // Для отображения загрузки
}

const ConfirmModal: React.FC<ConfirmModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  title = "Подтверждение",
  message,
  confirmText = "Да, удалить",
  cancelText = "Отмена",
  isLoading = false
}) => {

  if (!isOpen) {
    return null;
  }

  const handleConfirm = () => {
      // Не закрываем окно здесь, позволяем родительскому компоненту
      onConfirm();
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={title}>
        {/* Тело сообщения */}
        <div className="mb-6 text-gray-300">
            {message}
        </div>

        {/* Кнопки действий */}
        <div className="flex justify-end space-x-3 border-t border-gray-600 pt-4">
            <button
                type="button"
                onClick={onClose}
                disabled={isLoading} // Блокируем кнопку отмены во время загрузки подтверждения
                className="px-4 py-2 text-sm rounded bg-gray-600 hover:bg-gray-500 text-white disabled:opacity-50"
            >
                {cancelText}
            </button>
            <button
                type="button"
                onClick={handleConfirm}
                disabled={isLoading}
                className="px-4 py-2 text-sm rounded bg-red-600 hover:bg-red-700 text-white disabled:opacity-50 flex items-center" // Добавляем flex для спиннера
            >
                {isLoading && (
                    // Простой спиннер Tailwind
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                       <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                       <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                     </svg>
                )}
                {isLoading ? 'Удаление...' : confirmText}
            </button>
        </div>
    </Modal>
  );
};

export default ConfirmModal;