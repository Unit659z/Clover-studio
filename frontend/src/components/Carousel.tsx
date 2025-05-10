import React, { ReactNode, useId } from "react";
import { Swiper, SwiperSlide } from "swiper/react";
import { Navigation, Pagination, Autoplay, A11y } from "swiper/modules";

import "swiper/css";
import "swiper/css/navigation";
import "swiper/css/pagination";
import "swiper/css/autoplay";
import "swiper/css/a11y";

import "./Carousel.css";

interface CarouselProps<T> {
  items: T[];
  renderItem: (item: T, index: number) => ReactNode;
  slidesPerView?: number | "auto";
  spaceBetween?: number;
  loop?: boolean;
  autoplayDelay?: number;
  breakpoints?: {
    [width: number]: {
      slidesPerView?: number | "auto";
      spaceBetween?: number;
    };
    [ratio: string]: {
      slidesPerView?: number | "auto";
      spaceBetween?: number;
    };
  };
  className?: string;
}

function Carousel<T>({
  items,
  renderItem,
  slidesPerView = 1,
  spaceBetween = 30,
  loop = true,
  autoplayDelay = 5000,
  breakpoints,
  className = "",
}: CarouselProps<T>) {
  const carouselId = useId();
  const prevButtonClass = `swiper-button-prev-${carouselId}`;
  const nextButtonClass = `swiper-button-next-${carouselId}`;
  const paginationClass = `swiper-pagination-${carouselId}`;

  const autoplayConfig =
    autoplayDelay && autoplayDelay > 0
      ? {
          delay: autoplayDelay,
          disableOnInteraction: false,
          pauseOnMouseEnter: true,
        }
      : false;

  const enableLoop =
    loop &&
    items.length > (typeof slidesPerView === "number" ? slidesPerView : 1);
  const showNavigation =
    items.length > (typeof slidesPerView === "number" ? slidesPerView : 1);
  const showPagination = items.length > 1;

  return (
    <div className={`relative px-0 md:px-10 lg:px-12 ${className}`}>
      <Swiper
        modules={[Navigation, Pagination, Autoplay, A11y]}
        spaceBetween={spaceBetween}
        slidesPerView={slidesPerView}
        loop={enableLoop} // Используем вычисленное значение
        autoplay={autoplayConfig}
        navigation={
          showNavigation
            ? {
                nextEl: `.${nextButtonClass}`,
                prevEl: `.${prevButtonClass}`,
              }
            : false
        } // Отключаем, если слайдов мало
        pagination={
          showPagination
            ? {
                clickable: true,
                el: `.${paginationClass}`,
                bulletClass: "swiper-pagination-bullet-custom",
                bulletActiveClass: "swiper-pagination-bullet-active-custom",
              }
            : false
        } // Отключаем, если слайдов мало
        breakpoints={breakpoints}
        a11y={{
          prevSlideMessage: "Предыдущий слайд",
          nextSlideMessage: "Следующий слайд",
          paginationBulletMessage: "Перейти к слайду {{index}}",
        }}
        className="pb-12" // Отступ снизу для точек
      >
        {items.map((item, index) => (
          <SwiperSlide key={index}>{renderItem(item, index)}</SwiperSlide>
        ))}
      </Swiper>
      {showPagination && (
        <div
          className={`${paginationClass} swiper-pagination-custom-container`}
        ></div>
      )}
      {showNavigation && (
        <button
          className={`${prevButtonClass} swiper-button-prev-custom`}
        ></button>
      )}
      {showNavigation && (
        <button
          className={`${nextButtonClass} swiper-button-next-custom`}
        ></button>
      )}
    </div>
  );
}

export default Carousel;
