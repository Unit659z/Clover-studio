import axios, { AxiosHeaders } from 'axios'; 
import { getCookie } from '../utils/getCookie'; 

axios.defaults.baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
axios.defaults.withCredentials = true; // Оставляем для sessionid


axios.interceptors.request.use(
  (config) => {
    // Добавляем CSRF-токен для 'небезопасных' методов
    if (
      config.method &&
      ['post', 'put', 'patch', 'delete'].includes(config.method.toLowerCase())
    ) {
      // Пытаемся получить токен из куки
      const csrfToken = getCookie('csrftoken');

      if (csrfToken) {
         // Если токен найден, добавляем его в заголовок X-CSRFToken
         if (!config.headers) {
            config.headers = new AxiosHeaders();
          }
        config.headers['X-CSRFToken'] = csrfToken;
        console.log('CSRF token added to request header:', csrfToken); // Для отладки
      } else {
        console.warn('CSRF token not found in cookies for unsafe request.'); // Предупреждение
      }
    }
    return config; // Возвращаем измененную конфигурацию
  },
  (error) => {
    // Обработка ошибок конфигурации запроса
    return Promise.reject(error);
  }
);

// Импортируем и экспортируем getCookie 
export { getCookie }; 
export {}; 