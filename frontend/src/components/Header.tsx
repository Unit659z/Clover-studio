import React, { useState, useEffect, useRef } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const Header: React.FC = () => {
  const { isAuthenticated, currentUser, logout, cart } = useAuth();
  const navigate = useNavigate();
  const location = useLocation(); // Для отслеживания смены пути
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  const handleLogout = async () => {
    try {
      await logout();
      setIsMobileMenuOpen(false); // Закрываем меню после логаута
      navigate("/");
    } catch (error) {
      console.error("Logout failed from header:", error);
    }
  };

  const totalItemsInCart = cart?.total_items_count ?? 0;

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };

  // Закрытие меню при клике вне его
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsMobileMenuOpen(false);
      }
    };
    if (isMobileMenuOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    } else {
      document.removeEventListener("mousedown", handleClickOutside);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isMobileMenuOpen]);

  // Закрытие меню при изменении маршрута
  useEffect(() => {
    setIsMobileMenuOpen(false);
  }, [location.pathname]); 

  return (
    <header className="bg-[#181818] text-gray-300 sticky top-0 z-50 shadow-md">
      <nav className="container mx-auto px-4 py-3 flex justify-between items-center">
        {/* Logo */}
        <Link
          to="/"
          className="text-xl sm:text-2xl font-bold text-white flex items-center" 
          onClick={() => setIsMobileMenuOpen(false)} 
        >
          <img
            src="/images/clover.png"
            alt="Clover Studio Logo"
            className="mr-2 w-10 h-10 sm:w-14 sm:h-12"
          />{" "}
          Clover Studio
        </Link>
        <ul className="hidden md:flex space-x-6 items-center">
          <li>
            <Link to="/services" className="hover:text-white">
              Услуги
            </Link>
          </li>
          <li>
            <Link to="/portfolio" className="hover:text-white">
              Портфолио
            </Link>
          </li>
          <li>
            <Link to="/news" className="hover:text-white">
              Новости
            </Link>
          </li>
          <li>
            <a href="/#reviews" className="hover:text-white">
              Отзывы
            </a>
          </li>{" "}
        </ul>
        {/* --- Правая часть хедера: Иконка бургера и блок с кнопками/пользователем для десктопа --- */}
        <div className="flex items-center space-x-2">
          {/* Общий контейнер для правой части */}
          <div className="hidden md:flex items-center space-x-3">
            {isAuthenticated && currentUser ? (
              <>
                <Link
                  to="/account"
                  className="flex items-center space-x-2 hover:text-white"
                >
                  {currentUser.avatar_url ? (
                    <img
                      src={currentUser.avatar_url}
                      alt="avatar"
                      className="w-8 h-8 rounded-full object-cover border border-gray-500"
                    />
                  ) : (
                    <span className="w-8 h-8 rounded-full bg-gray-600 flex items-center justify-center border border-gray-500">
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        fill="none"
                        viewBox="0 0 24 24"
                        strokeWidth={1.5}
                        stroke="currentColor"
                        className="w-5 h-5 text-gray-300"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.501 20.118a7.5 7.5 0 0 1 14.998 0A17.933 17.933 0 0 1 12 21.75c-2.676 0-5.216-.584-7.499-1.632Z"
                        />
                      </svg>
                    </span>
                  )}
                  <span className="text-sm">
                    {currentUser.first_name || currentUser.username}
                  </span>
                </Link>
                {/* Иконка выхода для десктопа */}
                <button
                  onClick={handleLogout}
                  title="Выйти"
                  className="p-1 text-gray-400 hover:text-[#EB0000]"
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
                      d="M15.75 9V5.25A2.25 2.25 0 0 0 13.5 3h-6a2.25 2.25 0 0 0-2.25 2.25v13.5A2.25 2.25 0 0 0 7.5 21h6a2.25 2.25 0 0 0 2.25-2.25V15m3 0 3-3m0 0-3-3m3 3H9"
                    />
                  </svg>
                </button>
              </>
            ) : (
              <>
                <Link
                  to="/register"
                  className="text-sm border border-[#EB0000] text-[#EB0000] px-3 py-1.5 rounded hover:bg-[#EB0000] hover:text-white transition duration-300"
                >
                  Регистрация
                </Link>
                <Link
                  to="/login"
                  className="text-sm bg-[#EB0000] text-white px-4 py-1.5 rounded hover:bg-[#eb0000a0] transition duration-300"
                >
                  Вход
                </Link>
              </>
            )}
          </div>
          {/* Иконка корзины (видна всегда, когда не мобильное меню) */}
          <Link
            to="/cart"
            className="relative text-gray-300 hover:text-white p-1"
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
                d="M2.25 3h1.386c.51 0 .955.343 1.087.835l.383 1.437M7.5 14.25a3 3 0 0 0-3 3h15.75m-12.75-3h11.218c1.121-2.3 2.1-4.684 2.924-7.138a60.114 60.114 0 0 0-16.536-1.84M7.5 14.25 5.106 5.272M6 20.25a.75.75 0 1 1-1.5 0 .75.75 0 0 1 1.5 0Zm12.75 0a.75.75 0 1 1-1.5 0 .75.75 0 0 1 1.5 0Z"
              />
            </svg>
            {totalItemsInCart > 0 && (
              <span className="absolute -top-1 -right-1 bg-[#EB0000] text-white text-xs font-semibold rounded-full px-1.5 py-0.5 leading-none">
                {totalItemsInCart}
              </span>
            )}
          </Link>
          {/* Кнопка бургер-меню (только на мобильных) */}
          <button
            onClick={toggleMobileMenu}
            className="md:hidden p-1 text-gray-300 hover:text-white focus:outline-none"
            aria-label="Открыть меню"
            aria-expanded={isMobileMenuOpen}
          >
            {isMobileMenuOpen ? (
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
            ) : (
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
                  d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5"
                />
              </svg>
            )}
          </button>
        </div>{" "}
      </nav>

      {/* Мобильное меню */}
      <div
        ref={menuRef}
        className={`md:hidden absolute top-full left-0 right-0 bg-[#1c1c1c] shadow-lg transition-transform duration-300 ease-in-out overflow-y-auto
                   ${
                     isMobileMenuOpen
                       ? "max-h-[calc(100vh-4rem)] translate-y-0 py-4 border-t border-gray-700"
                       : "max-h-0 -translate-y-4 py-0 border-t border-transparent"
                   }`}
      >
        <ul className="flex flex-col items-center space-y-1 px-4">
          <li>
            <Link
              to="/services"
              onClick={toggleMobileMenu}
              className="block py-2.5 text-gray-300 hover:text-white w-full text-center"
            >
              Услуги
            </Link>
          </li>
          <li>
            <Link
              to="/portfolio"
              onClick={toggleMobileMenu}
              className="block py-2.5 text-gray-300 hover:text-white w-full text-center"
            >
              Портфолио
            </Link>
          </li>
          <li>
            <Link
              to="/news"
              onClick={toggleMobileMenu}
              className="block py-2.5 text-gray-300 hover:text-white w-full text-center"
            >
              Новости
            </Link>
          </li>
          <li>
            <a
              href="/#reviews"
              onClick={toggleMobileMenu}
              className="block py-2.5 text-gray-300 hover:text-white w-full text-center"
            >
              Отзывы
            </a>
          </li>
          <hr className="w-3/4 border-gray-600 my-2" />
          {isAuthenticated && currentUser ? (
            <>
              <li>
                <Link
                  to="/account"
                  onClick={toggleMobileMenu}
                  className="flex items-center justify-center space-x-2 py-2.5 text-gray-300 hover:text-white w-full text-center"
                >
                  {currentUser.avatar_url ? (
                    <img
                      src={currentUser.avatar_url}
                      alt="avatar"
                      className="w-6 h-6 rounded-full object-cover border border-gray-500"
                    />
                  ) : (
                    <span className="w-6 h-6 rounded-full bg-gray-600 flex items-center justify-center border border-gray-500">
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        fill="none"
                        viewBox="0 0 24 24"
                        strokeWidth={1.5}
                        stroke="currentColor"
                        className="w-4 h-4 text-gray-300"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.501 20.118a7.5 7.5 0 0 1 14.998 0A17.933 17.933 0 0 1 12 21.75c-2.676 0-5.216-.584-7.499-1.632Z"
                        />
                      </svg>
                    </span>
                  )}
                  <span>{currentUser.first_name || currentUser.username}</span>
                </Link>
              </li>
              <li>
                <button
                  onClick={() => {
                    handleLogout();
                    toggleMobileMenu();
                  }}
                  className="block py-2.5 text-red-500 hover:text-red-400 w-full text-center"
                >
                  Выйти
                </button>
              </li>
            </>
          ) : (
            <>
              <li>
                <Link
                  to="/register"
                  onClick={toggleMobileMenu}
                  className="block py-2.5 text-gray-300 hover:text-white w-full text-center"
                >
                  Регистрация
                </Link>
              </li>
              <li>
                <Link
                  to="/login"
                  onClick={toggleMobileMenu}
                  className="block py-2.5 text-gray-300 hover:text-white w-full text-center"
                >
                  Вход
                </Link>
              </li>
            </>
          )}
        </ul>
      </div>
    </header>
  );
};

export default Header;
