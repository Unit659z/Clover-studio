import React, { useState, FormEvent } from 'react';
import axios from 'axios';
import { useNavigate, Link } from 'react-router-dom';
import Header from '../components/Header';
import Footer from '../components/Footer';

interface PasswordChangeErrors {
    old_password?: string;
    new_password1?: string;
    new_password2?: string;
    non_field_errors?: string; // Общие ошибки
    api?: string; // Ошибка запроса
}

const PasswordChangePage: React.FC = () => {
  const [formData, setFormData] = useState({
    old_password: '',
    new_password1: '',
    new_password2: '',
  });
  const [errors, setErrors] = useState<PasswordChangeErrors>({});
  const [loading, setLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
    // Сбрасываем ошибки при изменении
    setErrors({});
    setSuccessMessage(null);
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrors({});
    setSuccessMessage(null);

    // Простая фронтенд валидация
    if (formData.new_password1 !== formData.new_password2) {
      setErrors({ new_password2: 'Новые пароли не совпадают.' });
      setLoading(false);
      return;
    }
    if (formData.new_password1.length < 6) { 
       setErrors({ new_password1: 'Новый пароль должен быть не менее 6 символов.' });
       setLoading(false);
       return;
    }

    try {
      // Отправляем POST запрос на бэкенд ( CSRF)
      const response = await axios.post('/studio/api/auth/password/change/', formData);
      setSuccessMessage(response.data.detail || 'Пароль успешно изменен!');
      // Очищаем форму после успеха
      setFormData({ old_password: '', new_password1: '', new_password2: '' });
      setTimeout(() => navigate('/account'), 2000);

    } catch (err: any) {
      const errorData = err.response?.data;
      const apiErrors: PasswordChangeErrors = {};
      let generalApiError = 'Ошибка смены пароля. Попробуйте снова.';

      if (errorData) {
        console.error("Password change error data:", errorData);
        if (errorData.detail) {
            generalApiError = errorData.detail;
        }
        // Распределяем ошибки по полям
        for (const key in errorData) {
          if (key !== 'detail' && Array.isArray(errorData[key])) {
            apiErrors[key as keyof PasswordChangeErrors] = errorData[key].join(', ');
          } else if (key !== 'detail' && typeof errorData[key] === 'string') {
               apiErrors[key as keyof PasswordChangeErrors] = errorData[key];
          }
        }
         if (Object.keys(apiErrors).length > 0) {
             generalApiError = "Обнаружены ошибки в полях.";
         }
      }
      apiErrors.api = generalApiError;
      setErrors(apiErrors);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-[#0D0C0C] text-gray-100 min-h-screen flex flex-col">
      <Header />
      <main className="flex-grow flex items-center justify-center container mx-auto px-4 py-8">
        <div className="bg-[#181818] p-8 rounded-lg shadow-xl w-full max-w-md">
          <h1 className="text-2xl font-bold text-white mb-6 text-center">Смена пароля</h1>
          <form onSubmit={handleSubmit} noValidate>
            {errors.api && <p className="mb-4 text-center text-red-500 text-sm">{errors.api}</p>}
            {successMessage && <p className="mb-4 text-center text-green-500 text-sm">{successMessage}</p>}

            {/* Старый пароль */}
            <div className="mb-4">
               <label htmlFor="old_password" className="block text-sm font-medium text-gray-400 mb-1">Старый пароль*</label>
               <input type="password" id="old_password" name="old_password" value={formData.old_password} onChange={handleChange} required
                  className={`w-full px-3 py-2 bg-gray-700 border rounded-md text-white focus:outline-none focus:ring-2 focus:ring-[#EB0000] ${errors.old_password ? 'border-red-500' : 'border-gray-600'}`}
                  autoComplete="current-password"
               />
               {errors.old_password && <p className="mt-1 text-xs text-red-500">{errors.old_password}</p>}
            </div>
            {/* Новый пароль */}
             <div className="mb-4">
                <label htmlFor="new_password1" className="block text-sm font-medium text-gray-400 mb-1">Новый пароль*</label>
                <input type="password" id="new_password1" name="new_password1" value={formData.new_password1} onChange={handleChange} required
                 placeholder="Не менее 6 символов"
                 className={`w-full px-3 py-2 bg-gray-700 border rounded-md text-white focus:outline-none focus:ring-2 focus:ring-[#EB0000] ${errors.new_password1 ? 'border-red-500' : 'border-gray-600'}`}
                 autoComplete="new-password"
                />
                 {errors.new_password1 && <p className="mt-1 text-xs text-red-500">{errors.new_password1}</p>}
             </div>
             {/* Подтверждение нового пароля */}
              <div className="mb-6">
                 <label htmlFor="new_password2" className="block text-sm font-medium text-gray-400 mb-1">Подтвердите новый пароль*</label>
                 <input type="password" id="new_password2" name="new_password2" value={formData.new_password2} onChange={handleChange} required
                  placeholder="Введите новый пароль еще раз"
                  className={`w-full px-3 py-2 bg-gray-700 border rounded-md text-white focus:outline-none focus:ring-2 focus:ring-[#EB0000] ${errors.new_password2 ? 'border-red-500' : 'border-gray-600'}`}
                  autoComplete="new-password"
                 />
                  {errors.new_password2 && <p className="mt-1 text-xs text-red-500">{errors.new_password2}</p>}
              </div>

            <div className="flex justify-between items-center mt-6">
                <Link to="/account" className="text-sm text-gray-400 hover:text-[#EB0000] underline">
                    Отмена
                </Link>
                <button
                  type="submit"
                  disabled={loading}
                  className="bg-[#EB0000] text-white py-2 px-6 rounded hover:bg-[#eb0000a0] transition duration-300 disabled:opacity-50"
                >
                  {loading ? 'Сохранение...' : 'Изменить пароль'}
                </button>
            </div>
          </form>
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default PasswordChangePage;