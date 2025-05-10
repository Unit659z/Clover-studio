import React, { useState, FormEvent, ChangeEvent } from "react";
import { useNavigate, Link } from "react-router-dom";
import axios from "axios";
import Header from "../components/Header";
import Footer from "../components/Footer";
import { useAuth } from "../context/AuthContext";

// Интерфейс для ошибок формы
interface FormErrors {
  username?: string;
  email?: string;
  password?: string;
  password2?: string;
  api?: string; // Общая ошибка API
}

const RegisterPage: React.FC = () => {
  const [formData, setFormData] = useState({
    username: "",
    email: "",
    password: "",
    password2: "",
    first_name: "",
    last_name: "",
    phone_number: "",
  });
  // Состояние для ошибок валидации фронтенда и API
  const [errors, setErrors] = useState<FormErrors>({});
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { checkAuthStatus } = useAuth();

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};
    let isValid = true;

    if (!formData.username.trim()) {
      newErrors.username = "Имя пользователя обязательно.";
      isValid = false;
    }
    if (!formData.email.trim() || !/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = "Введите корректный email.";
      isValid = false;
    }
    if (formData.password.length < 6) {
      newErrors.password = "Пароль должен быть не менее 8 символов.";
      isValid = false;
    }
    if (formData.password !== formData.password2) {
      newErrors.password2 = "Пароли не совпадают.";
      isValid = false;
    }

    setErrors(newErrors);
    return isValid;
  };

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
    if (errors[name as keyof FormErrors]) {
      setErrors((prev) => ({ ...prev, [name]: undefined }));
    }
    if (errors.api) {
      setErrors((prev) => ({ ...prev, api: undefined }));
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    // Сначала валидация на фронте
    if (!validateForm()) {
      return; // Не отправляем, если есть ошибки фронтенда
    }

    setLoading(true);
    setErrors({}); // Сбрасываем все ошибки перед отправкой

    try {
      // Отправляем запрос на регистрацию
      const response = await axios.post("/studio/api/auth/register/", formData);
      console.log(
        "Registration successful, user should be logged in:",
        response.data
      );

      // Обновляем статус
      await checkAuthStatus();

      // Перенаправляем в личный кабинет
      navigate("/account");
    } catch (err: any) {
      const errorData = err.response?.data;
      const apiErrors: FormErrors = {};
      let generalApiError =
        "Ошибка регистрации. Пожалуйста, проверьте введенные данные.";

      if (errorData) {
        console.error("Registration error data:", errorData);
        let fieldErrorMessages: string[] = [];
        // Собираем ошибки по полям из ответа бэкенда
        for (const key in errorData) {
          if (key === "detail") {
            generalApiError = errorData.detail;
          } else if (Array.isArray(errorData[key])) {
            apiErrors[key as keyof FormErrors] = errorData[key].join(", ");
            fieldErrorMessages.push(`${key}: ${errorData[key].join(", ")}`);
          } else if (typeof errorData[key] === "string") {
            apiErrors[key as keyof FormErrors] = errorData[key];
            fieldErrorMessages.push(`${key}: ${errorData[key]}`);
          }
        }
        // Если были ошибки по полям, но нет общей, формируем общую
        if (
          fieldErrorMessages.length > 0 &&
          generalApiError ===
            "Ошибка регистрации. Пожалуйста, проверьте введенные данные."
        ) {
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
          <h1 className="text-2xl font-bold text-white mb-6 text-center">
            Регистрация
          </h1>
          <form onSubmit={handleSubmit} noValidate>
            {errors.api && (
              <p className="mb-4 text-center text-red-500 text-sm">
                {errors.api}
              </p>
            )}

            {/* Username */}
            <div className="mb-4">
              <label
                htmlFor="username"
                className="block text-sm font-medium text-gray-400 mb-1"
              >
                Имя пользователя*
              </label>
              <input
                type="text"
                id="username"
                name="username"
                value={formData.username}
                onChange={handleChange}
                required
                placeholder="Придумайте имя пользователя"
                className={`w-full px-3 py-2 bg-gray-700 border rounded-md text-white focus:outline-none focus:ring-2 focus:ring-[#EB0000] ${
                  errors.username ? "border-red-500" : "border-gray-600"
                }`}
              />
              {/* Отображаем ошибку поля */}
              {errors.username && (
                <p className="mt-1 text-xs text-red-500">{errors.username}</p>
              )}
            </div>
            {/* Email */}
            <div className="mb-4">
              <label
                htmlFor="email"
                className="block text-sm font-medium text-gray-400 mb-1"
              >
                Email*
              </label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                required
                placeholder="your.email@example.com"
                className={`w-full px-3 py-2 bg-gray-700 border rounded-md text-white focus:outline-none focus:ring-2 focus:ring-[#EB0000] ${
                  errors.email ? "border-red-500" : "border-gray-600"
                }`}
              />
              {errors.email && (
                <p className="mt-1 text-xs text-red-500">{errors.email}</p>
              )}
            </div>
            {/* Password */}
            <div className="mb-4">
              <label
                htmlFor="password"
                className="block text-sm font-medium text-gray-400 mb-1"
              >
                Пароль*
              </label>
              <input
                type="password"
                id="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                required
                placeholder="Не менее 6 символов"
                className={`w-full px-3 py-2 bg-gray-700 border rounded-md text-white focus:outline-none focus:ring-2 focus:ring-[#EB0000] ${
                  errors.password ? "border-red-500" : "border-gray-600"
                }`}
                autoComplete="new-password"
              />
              {errors.password && (
                <p className="mt-1 text-xs text-red-500">{errors.password}</p>
              )}
            </div>
            {/* Password Confirmation */}
            <div className="mb-6">
              <label
                htmlFor="password2"
                className="block text-sm font-medium text-gray-400 mb-1"
              >
                Подтвердите пароль*
              </label>
              <input
                type="password"
                id="password2"
                name="password2"
                value={formData.password2}
                onChange={handleChange}
                required
                placeholder="Введите пароль еще раз"
                className={`w-full px-3 py-2 bg-gray-700 border rounded-md text-white focus:outline-none focus:ring-2 focus:ring-[#EB0000] ${
                  errors.password2 ? "border-red-500" : "border-gray-600"
                }`}
                autoComplete="new-password"
              />
              {errors.password2 && (
                <p className="mt-1 text-xs text-red-500">{errors.password2}</p>
              )}
            </div>
            {/* Optional Fields */}
            <hr className="border-gray-600 my-4" />
            <div className="mb-4">
              <label
                htmlFor="first_name"
                className="block text-sm font-medium text-gray-400 mb-1"
              >
                Имя
              </label>
              <input
                type="text"
                id="first_name"
                name="first_name"
                value={formData.first_name}
                onChange={handleChange}
                placeholder="(необязательно)"
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-[#EB0000]"
              />
            </div>
            <div className="mb-4">
              <label
                htmlFor="last_name"
                className="block text-sm font-medium text-gray-400 mb-1"
              >
                Фамилия
              </label>
              <input
                type="text"
                id="last_name"
                name="last_name"
                value={formData.last_name}
                onChange={handleChange}
                placeholder="(необязательно)"
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-[#EB0000]"
              />
            </div>
            <div className="mb-6">
              <label
                htmlFor="phone_number"
                className="block text-sm font-medium text-gray-400 mb-1"
              >
                Телефон
              </label>
              <input
                type="tel"
                id="phone_number"
                name="phone_number"
                value={formData.phone_number}
                onChange={handleChange}
                placeholder="(необязательно)"
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-[#EB0000]"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-[#EB0000] text-white py-2 px-4 rounded hover:bg-[#eb0000a0] transition duration-300 disabled:opacity-50"
            >
              {loading ? "Регистрация..." : "Зарегистрироваться"}
            </button>
          </form>
          <p className="mt-6 text-center text-sm text-gray-400">
            Уже есть аккаунт?{" "}
            <Link to="/login" className="text-[#EB0000] hover:underline">
              Войти
            </Link>
          </p>
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default RegisterPage;
