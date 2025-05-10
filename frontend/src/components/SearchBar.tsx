// src/components/SearchBar.tsx
import React, { useState, useEffect, ChangeEvent, useRef } from "react";

interface SearchBarProps {
  onSearchChange: (searchTerm: string) => void;
  placeholder?: string;
  initialValue?: string;
  debounceTimeout?: number;
}

const SearchBar: React.FC<SearchBarProps> = ({
  onSearchChange,
  placeholder = "Поиск услуг...",
  initialValue = "",
  debounceTimeout = 500,
}) => {
  // Локальное состояние для поля ввода, инициализируем из initialValue
  const [inputValue, setInputValue] = useState(initialValue);
  const debounceTimer = useRef<NodeJS.Timeout | null>(null);
  const isMounted = useRef(false);

  // Синхронизируем локальное состояние с initialValue из URL,
  // если оно изменилось извне (например, кнопкой "Назад")
  useEffect(() => {
    if (isMounted.current) {
      // Только если значение из URL НЕ совпадает с текущим в инпуте
      if (initialValue !== inputValue) {
        console.log(
          `SearchBar useEffect: Syncing inputValue (${inputValue}) to initialValue (${initialValue}) from URL`
        ); // Отладка
        setInputValue(initialValue);
      }
    } else {
      isMounted.current = true; // Отмечаем, что первый рендер прошел
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialValue]);

  // Обработчик изменения в поле ввода
  const handleChange = (event: ChangeEvent<HTMLInputElement>) => {
    const newValue = event.target.value;
    setInputValue(newValue); // Обновляем локальное состояние

    // Очищаем предыдущий таймер, если он есть
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }

    // Запускаем новый таймер
    debounceTimer.current = setTimeout(() => {
      console.log(
        `SearchBar Debounce: Calling onSearchChange with "${newValue}"`
      ); // Отладка
      onSearchChange(newValue); // Вызываем колбэк с новым значением ПОСЛЕ задержки
    }, debounceTimeout);
  };

  // Очистка таймера
  useEffect(() => {
    return () => {
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current);
      }
    };
  }, []);

  return (
    <div className="relative w-full max-w-xl mx-auto">
      <input
        type="text"
        value={inputValue}
        onChange={handleChange}
        placeholder={placeholder}
        className="w-full px-4 py-2 pr-10 bg-[#181818] border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-[#EB0000] placeholder-gray-500"
      />
      <svg
        className="absolute right-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-500"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="2"
          d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
        />
      </svg>
    </div>
  );
};

export default SearchBar;
