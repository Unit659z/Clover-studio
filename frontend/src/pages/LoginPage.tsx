import React, { useState, FormEvent } from "react";
import { useAuth } from "../context/AuthContext";
import { useNavigate, Link } from "react-router-dom";
import Header from "../components/Header";
import Footer from "../components/Footer";

const LoginPage: React.FC = () => {
  // Используем одно состояние для идентификатора
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const { login } = useAuth(); // login из контекста вызывает наш API
  const navigate = useNavigate();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await login({
        identifier: identifier,
        password: password,
      });
      navigate("/account");
    } catch (err: any) {
      // Обработка ошибок
      const errorData = err.response?.data;
      let errorMessage = "Ошибка входа. Проверьте данные и попробуйте снова.";
      if (errorData && errorData.detail) {
        errorMessage = errorData.detail;
      } else if (errorData) {
        console.error("Login error data:", errorData);
      }
      setError(errorMessage);
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
            Вход
          </h1>
          <form onSubmit={handleSubmit}>
            {error && (
              <p className="mb-4 text-center text-red-500 text-sm">{error}</p>
            )}
            <div className="mb-4">
              <label
                htmlFor="identifier"
                className="block text-sm font-medium text-gray-400 mb-1"
              >
                Имя пользователя или Email
              </label>
              <input
                type="text"
                id="identifier"
                value={identifier}
                onChange={(e) => setIdentifier(e.target.value)}
                required
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-[#EB0000]"
                autoComplete="username email"
              />
            </div>
            <div className="mb-6">
              <label
                htmlFor="password"
                className="block text-sm font-medium text-gray-400 mb-1"
              >
                Пароль
              </label>
              <input
                type="password"
                id="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-[#EB0000]"
                autoComplete="current-password"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-[#EB0000] text-white py-2 px-4 rounded hover:bg-[#eb0000a0] transition duration-300 disabled:opacity-50"
            >
              {loading ? "Вход..." : "Войти"}
            </button>
          </form>
          <p className="mt-6 text-center text-sm text-gray-400">
            Нет аккаунта?{" "}
            <Link to="/register" className="text-[#EB0000] hover:underline">
              Зарегистрироваться
            </Link>
          </p>
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default LoginPage;
