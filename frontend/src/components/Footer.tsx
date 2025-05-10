import React from "react";
import { Link } from "react-router-dom";

const Footer: React.FC = () => {
  return (
    <footer className="bg-[#181818] text-gray-400 pt-10 pb-6 mt-16">
      <div className="container mx-auto px-4">
        <div className="flex flex-wrap justify-between items-center mb-8">
          <a
            href="/"
            className="text-xl font-bold text-white flex items-center mb-4 sm:mb-0"
          >
            <img
              src="/images/clover.png"
              alt="Видеомонтажер за работой"
              className="mr-2 w-14"
            />
            Clover Studio
          </a>
          <ul className="flex flex-wrap space-x-6 text-sm">
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
            </li>
          </ul>
        </div>
        <div className="border-t border-gray-700 pt-6 flex flex-col sm:flex-row justify-between items-center text-xs">
          <span className="mx-auto">
            © 2025 Видеостудия Clover Studio. Все права защищены.
          </span>
          <div className="flex space-x-4 mt-4 sm:mt-0">
            <a
              href="#"
              target="_blank"
              rel="noopener noreferrer"
              aria-label="VK"
              className="w-7 h-7"
            >
              {" "}
              <img
                src="/images/vk-icon.png"
                alt="VK"
                className="w-full h-full object-contain"
              />{" "}
            </a>
            <a
              href="#"
              target="_blank"
              rel="noopener noreferrer"
              aria-label="Telegram"
              className="w-7 h-7"
            >
              <img
                src="/images/tg-icon.png"
                alt="Telegram"
                className="w-full h-full object-contain"
              />
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
