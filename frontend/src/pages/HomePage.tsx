import React, { useState, useEffect } from "react";
import axios from "axios";
import { Link } from "react-router-dom";
import Header from "../components/Header";
import Footer from "../components/Footer";
import ServiceCard from "../components/ServiceCard";
import PortfolioCard from "../components/PortfolioCard";
import ReviewCard from "../components/ReviewCard";
import Carousel from "../components/Carousel";
import {
  Service,
  PortfolioItem,
  Review,
} from "../interfaces";

interface StatsData {
  total_users: number;
  completed_orders: number;
}

const placeholderServiceImage = "/images/placeholder-service.png";

const HomePage: React.FC = () => {
  const [services, setServices] = useState<Service[]>([]);
  const [portfolioItems, setPortfolioItems] = useState<PortfolioItem[]>([]);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [stats, setStats] = useState<StatsData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await axios.get('/studio/api/home-page-data/');

        setServices(response.data.services);
        setPortfolioItems(response.data.portfolio_items);
        setReviews(response.data.reviews);
        setStats(response.data.stats);

      } catch (err: any) {
        console.error("Error fetching data:", err);
        setError(
          err.message ||
            "Не удалось загрузить данные. Попробуйте обновить страницу."
        );
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen bg-[#0D0C0C] text-white">
        Загрузка...
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex justify-center items-center min-h-screen bg-[#0D0C0C] text-[#EB0000]">
        Ошибка: {error}
      </div>
    );
  }

  return (
    <div className="bg-[#0D0C0C] text-gray-100 min-h-screen font-sans">
      <Header />

      <main className="container mx-auto px-4 py-8 md:py-12">
        {/* Начало */}
        <section className="container mx-auto px-4 py-8 md:py-12 grid md:grid-cols-2 gap-8 md:gap-12 items-center mb-16 md:mb-24 ">
          <div>
            <img
              src="/images/hero-image.jpg"
              alt="Видеомонтажер за работой"
              className="rounded-lg shadow-xl w-full h-auto object-cover"
            />
          </div>
          <div className="text-center md:text-left">
            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-white mb-4">
              Мы лучшие в видеомонтаже
            </h1>
            <div className="w-4/4 h-1 bg-[#EB0000] mb-6 mx-auto md:mx-0"></div>
            <p className="text-gray-300 leading-relaxed">
              Мы — команда опытных видеомонтажеров, работающих с современным
              оборудованием и новейшими технологиями монтажа. Наш подход
              сочетает креативность и внимание к деталям, что позволяет нам
              создавать видео, которые действительно привлекают внимание и
              передают нужные эмоции. Мы работаем с проектами для самых разных
              сфер — от рекламных и корпоративных видео до контента для
              социальных сетей. Наша цель — помочь нашим клиентам выделиться и
              сделать их идеи яркими и запоминающимися.
            </p>
          </div>
        </section>

        {stats && (
            <section className="mb-16 md:mb-24 bg-[#181818] py-8 px-4 rounded-lg shadow-xl border border-gray-800">
                <div className="max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-8 text-center">
                    <div>
                        <p className="text-4xl lg:text-5xl font-bold text-[#EB0000]">{stats.total_users}</p>
                        <p className="text-gray-400 mt-2">Зарегистрированных пользователей</p>
                    </div>
                    <div>
                        <p className="text-4xl lg:text-5xl font-bold text-[#EB0000]">{stats.completed_orders}</p>
                        <p className="text-gray-400 mt-2">Выполненных заказов</p>
                    </div>
                </div>
            </section>
        )}

        {/* Services Section */}
        <section
          id="services"
          className="container mx-auto px-4 md:px-10 lg:px-14 xl:px-16 mb-16 md:mb-24"
        >
          <h2 className="text-3xl font-bold text-center text-white mb-3">
            Наши услуги
          </h2>
          <p className="text-center text-gray-400 mb-6 max-w-2xl mx-auto">
            Мы предоставляем премиальные услуги...
          </p>
          <div className="text-center mb-10">
            <Link
              to="/services"
              className="bg-[#EB0000] text-white px-6 py-2 rounded hover:bg-[#eb0000a0] transition duration-300" // Копируем классы
            >
              Узнать больше
            </Link>
          </div>
          {/*  Карусель */}
          {services.length > 0 ? (
            <Carousel
              items={services}
              renderItem={(service) => (
                <ServiceCard
                  serviceId={service.pk}
                  key={service.pk}
                  imageUrl={service.photo_url || placeholderServiceImage}
                  title={service.name}
                />
              )}
              // Настройки отображения слайдов
              slidesPerView={1}
              spaceBetween={20}
              autoplayDelay={4000}
              breakpoints={{
                // Адаптивность
                640: {
                  // sm
                  slidesPerView: 2,
                  spaceBetween: 20,
                },
                1024: {
                  // lg
                  slidesPerView: 3,
                  spaceBetween: 30,
                },
              }}
            />
          ) : (
            !loading && (
              <p className="text-center text-gray-500">
                Услуги пока не добавлены.
              </p>
            )
          )}
        </section>

        {/* Portfolio Section */}
        <section
          id="portfolio"
          className="container mx-auto px-4 md:px-10 lg:px-14 xl:px-16 mb-16 md:mb-24"
        >
          <h2 className="text-3xl font-bold text-center text-white mb-3">
            Наши работы
          </h2>
          <p className="text-center text-gray-400 mb-6 max-w-2xl mx-auto">
            Мы поддерживаем максимальное качество...
          </p>
          <div className="text-center mb-10">
            <Link
              to="/portfolio"
              className="bg-[#EB0000] text-white px-6 py-2 rounded hover:bg-[#eb0000a0] transition duration-300" // Копируем классы
            >
              Узнать больше
            </Link>
          </div>
          {/* Карусель */}
          {portfolioItems.length > 0 ? (
            <Carousel
              items={portfolioItems}
              renderItem={(item) => (
                <PortfolioCard
                  pk={item.pk}
                  key={item.pk}
                  image_url={item.image_url}
                  title={item.title}
                />
              )}
              slidesPerView={1}
              spaceBetween={30}
              autoplayDelay={5500}
              breakpoints={{
                768: {
                  // md
                  slidesPerView: 2,
                  spaceBetween: 30,
                },
              }}
            />
          ) : (
            !loading && (
              <p className="text-center text-gray-500">
                Работы в портфолио пока не добавлены.
              </p>
            )
          )}
        </section>

        {/* Отзывы */}
        <section
          id="reviews"
          className="container mx-auto px-4 md:px-10 lg:px-14 xl:px-16 mb-16 md:mb-24"
        >
          <h2 className="text-3xl font-bold text-center text-white mb-10">
            Отзывы
          </h2>
          {/* Отображаем данные из API */}
          {/*Используем Карусель*/}
          {reviews.length > 0 ? (
            <Carousel
              items={reviews}
              renderItem={(review) => (
                <div className="h-full">
                  <ReviewCard
                    key={review.pk}
                    avatar_url={review.user_read?.avatar_url}
                    name={
                      review.user_read?.full_name ||
                      review.user_read?.username ||
                      "Аноним"
                    }
                    stars={review.rating}
                    reviewText={review.comment}
                  />
                </div>
              )}
              slidesPerView={1}
              spaceBetween={20}
              autoplayDelay={5000}
              breakpoints={{
                640: {
                  // sm
                  slidesPerView: 2,
                  spaceBetween: 20,
                },
                1024: {
                  // lg
                  slidesPerView: 3,
                  spaceBetween: 30,
                },
              }}
            />
          ) : (
            !loading && (
              <p className="text-center text-gray-500">Отзывов пока нет.</p>
            )
          )}
        </section>
      </main>

      <Footer />
    </div>
  );
};

export default HomePage;
