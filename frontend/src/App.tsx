import React from "react";
import { Routes, Route } from "react-router-dom";
import HomePage from "./pages/HomePage";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import AccountPage from "./pages/AccountPage";
import ServicesPage from "./pages/ServicesPage";
import PortfolioPage from "./pages/PortfolioPage";
import ServiceDetailPage from "./pages/ServiceDetailPage";
import PrivateRoute from "./components/PrivateRoute";
import PortfolioDetailPage from "./pages/PortfolioDetailPage";
import PasswordChangePage from "./pages/PasswordChangePage";
import CartPage from "./pages/CartPage";
import NotificationCenter from "./components/NotificationCenter";
import NewsPage from "./pages/NewsPage";
import "./index.css";

function App() {
  return (
    <>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/services" element={<ServicesPage />} />
        <Route path="/services/:pk" element={<ServiceDetailPage />} />
        <Route path="/portfolio" element={<PortfolioPage />} />
        <Route path="/portfolio/:pk" element={<PortfolioDetailPage />} />
        <Route path="/news" element={<NewsPage />} />
        {/* Приватные маршруты */}
        <Route element={<PrivateRoute />}>
          <Route path="/account" element={<AccountPage />} />
          <Route path="/password-change" element={<PasswordChangePage />} />
          <Route path="/cart" element={<CartPage />} />
        </Route>
      </Routes>
      <NotificationCenter />
    </>
  );
}

export default App;
