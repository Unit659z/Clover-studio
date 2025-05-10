import React, { useState, useEffect, FormEvent, ChangeEvent } from "react";
import { useAuth } from "../context/AuthContext";
import axios from "axios";
import Header from "../components/Header";
import Footer from "../components/Footer";
import Modal from "../components/Modal";
import OrderDetailContent from "../components/OrderDetailContent";
import { Order, UserProfile } from "../interfaces";
import { Link } from "react-router-dom";

interface AccountFormData {
  first_name: string;
  last_name: string;
  email: string;
  phone_number: string | null;
}

const AccountPage: React.FC = () => {
  const { currentUser, logout, updateUserProfile, isAuthLoading } = useAuth();
  const [orders, setOrders] = useState<Order[]>([]);
  const [loadingOrders, setLoadingOrders] = useState(false);
  const [ordersError, setOrdersError] = useState<string | null>(null);
  const [formData, setFormData] = useState<AccountFormData>({
    first_name: "",
    last_name: "",
    email: "",
    phone_number: null,
  });
  const [isEditing, setIsEditing] = useState(false);
  const [updateLoading, setUpdateLoading] = useState(false);
  const [updateError, setUpdateError] = useState<string | null>(null);
  const [updateSuccess, setUpdateSuccess] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [selectedAvatarFile, setSelectedAvatarFile] = useState<File | null>(
    null
  );
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null);

  useEffect(() => {
    if (currentUser) {
      setFormData({
        first_name: currentUser.first_name || "",
        last_name: currentUser.last_name || "",
        email: currentUser.email || "",
        phone_number: currentUser.phone_number || null,
      });
      setAvatarPreview(currentUser.avatar_url || null);
      setSelectedAvatarFile(null);
      setIsEditing(false);
    }
  }, [currentUser]);

  useEffect(() => {
    const fetchOrders = async () => {
      if (!currentUser) return;
      setLoadingOrders(true);
      setOrdersError(null);
      try {
        const response = await axios.get<{ results: Order[] }>(
          "/studio/api/orders/"
        );
        setOrders(response.data.results);
      } catch (err) {
        console.error("Error fetching orders:", err);
        setOrdersError("Не удалось загрузить заказы.");
      } finally {
        setLoadingOrders(false);
      }
    };
    if (currentUser) {
      fetchOrders();
    } else {
      setOrders([]);
      setLoadingOrders(false);
      setOrdersError(null);
    }
  }, [currentUser]);

  const handleAvatarChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedAvatarFile(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setAvatarPreview(reader.result as string);
      };
      reader.readAsDataURL(file);
      if (!isEditing) setIsEditing(true);
      setUpdateSuccess(null);
      setUpdateError(null);
    }
  };

  const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    if (!isEditing) setIsEditing(true);
    setUpdateSuccess(null);
    setUpdateError(null);
  };

  const handleProfileUpdate = async (e: FormEvent) => {
    e.preventDefault();
    if (!isEditing && !selectedAvatarFile) return;
    setUpdateLoading(true);
    setUpdateError(null);
    setUpdateSuccess(null);

    const submissionData = new FormData();
    let hasChanges = false;

    for (const key in formData) {
      if (
        formData[key as keyof AccountFormData] !==
        currentUser?.[key as keyof UserProfile]
      ) {
        const valueToAppend =
          key === "phone_number" && !formData[key as keyof AccountFormData]
            ? ""
            : formData[key as keyof AccountFormData];
        if (valueToAppend !== null) {
          submissionData.append(key, valueToAppend as string);
          hasChanges = true;
        }
      }
    }

    if (selectedAvatarFile) {
      submissionData.append("avatar", selectedAvatarFile);
      hasChanges = true;
    }

    if (!hasChanges) {
      setUpdateSuccess("Нет изменений для сохранения.");
      setUpdateLoading(false);
      setIsEditing(false);
      return;
    }

    console.log("Sending update data:", Object.fromEntries(submissionData)); // Отладка FormData

    try {
      await updateUserProfile(submissionData);
      setUpdateSuccess("Данные успешно сохранены!");
      setIsEditing(false);
      setSelectedAvatarFile(null);
    } catch (err: any) {
      const errorData = err.response?.data;
      let errorMessage = "Ошибка сохранения данных.";
      if (errorData) {
        console.error("Profile update error data:", errorData);
        errorMessage = Object.entries(errorData)
          .map(([key, value]) => {})
          .filter(Boolean)
          .join("; ");
        if (!errorMessage && errorData.detail) {
          errorMessage = errorData.detail;
        }
        if (!errorMessage) {
          errorMessage = "Неизвестная ошибка сохранения.";
        }
      }
      setUpdateError(errorMessage);
    } finally {
      setUpdateLoading(false);
    }
  };

  const openModal = (order: Order) => {
    setSelectedOrder(order);
    setIsModalOpen(true);
  };
  const closeModal = () => {
    setIsModalOpen(false);
    setSelectedOrder(null);
  };

  if (isAuthLoading) {
    return (
      <div className="flex justify-center items-center min-h-screen bg-[#0D0C0C] text-white">
        Загрузка данных пользователя...
      </div>
    );
  }
  if (!currentUser) {
    return (
      <div className="flex justify-center items-center min-h-screen bg-[#0D0C0C] text-white">
        Пользователь не найден. Пожалуйста, войдите снова.
      </div>
    );
  }

  return (
    <div className="bg-[#0D0C0C] text-gray-100 min-h-screen flex flex-col">
      <Header />
      <main className="flex-grow container mx-auto px-4 py-8 md:py-12">
        <h1 className="text-3xl font-bold text-white mb-8">Личный кабинет</h1>
        <div className="flex flex-col md:flex-row gap-8">
          {" "}
          {/* Левая колонка: Заказы */}
          <div className="w-full md:w-2/3 bg-[#181818] p-6 rounded-lg shadow-xl border border-gray-700">
            <h2 className="text-xl font-semibold text-white mb-4">
              Ваши заказы
            </h2>
            <div className="border border-gray-500 rounded-md min-h-[300px] p-4">
              {loadingOrders && (
                <p className="text-center text-gray-400">Загрузка заказов...</p>
              )}
              {ordersError && (
                <p className="text-center text-red-500">{ordersError}</p>
              )}
              {!loadingOrders && !ordersError && orders.length === 0 && (
                <p className="text-gray-400 text-center text-lg pt-20">
                  Здесь пока что ничего нет...
                </p>
              )}
              {!loadingOrders && !ordersError && orders.length > 0 && (
                <ul className="space-y-3 w-full">
                  {orders.map((order) => (
                    <li
                      key={order.pk}
                      className="bg-gray-700 p-3 rounded text-sm flex flex-col sm:flex-row justify-between sm:items-center space-y-2 sm:space-y-0"
                    >
                      <div className="flex-grow mr-0 sm:mr-4 text-center sm:text-left">
                        <span className="font-medium block sm:inline">
                          Заказ #{order.pk}
                        </span>
                        <span className="block text-xs text-gray-400 mt-1 sm:mt-0 sm:ml-2">
                          {order.service?.name || "Услуга удалена"}
                          {" от "}
                          {new Date(order.created_at).toLocaleDateString(
                            "ru-RU"
                          )}
                        </span>
                      </div>
                      <div className="flex items-center justify-center sm:justify-end space-x-3 flex-shrink-0 mt-2 sm:mt-0">
                        <span
                          className={`font-medium px-2 py-0.5 rounded text-xs whitespace-nowrap ${
                            order.status?.status_name === "completed"
                              ? "bg-green-600 text-white"
                              : order.status?.status_name === "cancelled"
                              ? "bg-red-700 text-white"
                              : order.status?.status_name === "processing"
                              ? "bg-orange-600 text-white"
                              : "bg-blue-600 text-white"
                          }`}
                        >
                          {order.status?.display_name || "Статус неизвестен"}
                        </span>
                        <button
                          onClick={() => openModal(order)}
                          className="text-xs bg-[#EB0000] text-white px-3 py-1 rounded hover:bg-[#eb0000a0] transition duration-300 whitespace-nowrap"
                        >
                          Подробнее
                        </button>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
          {/* Правая колонка: Данные пользователя */}
          <div className="w-full md:w-1/3">
            <div className="bg-[#181818] p-6 rounded-lg shadow-xl h-full md:h-auto">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-semibold text-white">
                  Ваши данные
                </h2>
                <button
                  onClick={logout}
                  className="text-sm text-[#EB0000] hover:underline"
                >
                  Выйти
                </button>
              </div>
              <form onSubmit={handleProfileUpdate}>
                {updateError && (
                  <p className="mb-4 text-center text-red-500 text-sm whitespace-pre-line">
                    {updateError.replace(/;/g, "\n")}
                  </p>
                )}
                {updateSuccess && (
                  <p className="mb-4 text-center text-green-500 text-sm">
                    {updateSuccess}
                  </p>
                )}
                <div className="mb-6 text-center">
                  <img
                    src={avatarPreview || "/images/placeholder-avatar.png"}
                    alt="Аватар"
                    className="w-24 h-24 md:w-32 md:h-32 rounded-full mx-auto object-cover border-2 border-gray-500 mb-3"
                  />
                  <label
                    htmlFor="avatar-upload"
                    className="cursor-pointer text-sm text-[#EB0000] hover:underline"
                  >
                    Сменить фото
                  </label>
                  <input
                    type="file"
                    id="avatar-upload"
                    name="avatar"
                    accept="image/*"
                    onChange={handleAvatarChange}
                    className="hidden"
                  />
                </div>
                <div className="mb-5 relative">
                  <label className="absolute -top-3 left-2 bg-[#181818] px-1 text-xs text-gray-400">
                    Фамилия
                  </label>
                  <input
                    type="text"
                    name="last_name"
                    value={formData.last_name || ""}
                    onChange={handleInputChange}
                    className="w-full bg-transparent border-b border-gray-500 py-2 px-1 text-white focus:outline-none focus:border-[#EB0000]"
                  />
                </div>
                <div className="mb-5 relative">
                  <label className="absolute -top-3 left-2 bg-[#181818] px-1 text-xs text-gray-400">
                    Имя
                  </label>
                  <input
                    type="text"
                    name="first_name"
                    value={formData.first_name || ""}
                    onChange={handleInputChange}
                    className="w-full bg-transparent border-b border-gray-500 py-2 px-1 text-white focus:outline-none focus:border-[#EB0000]"
                  />
                </div>
                <div className="mb-5 relative">
                  <label className="absolute -top-3 left-2 bg-[#181818] px-1 text-xs text-gray-400">
                    Электронная почта
                  </label>
                  <input
                    type="email"
                    name="email"
                    value={formData.email || ""}
                    onChange={handleInputChange}
                    required
                    className="w-full bg-transparent border-b border-gray-500 py-2 px-1 text-white focus:outline-none focus:border-[#EB0000]"
                  />
                </div>
                <div className="mb-6 relative">
                  <label className="absolute -top-3 left-2 bg-[#181818] px-1 text-xs text-gray-400">
                    Мобильный телефон
                  </label>
                  <input
                    type="tel"
                    name="phone_number"
                    value={formData.phone_number || ""}
                    onChange={handleInputChange}
                    className="w-full bg-transparent border-b border-gray-500 py-2 px-1 text-white focus:outline-none focus:border-[#EB0000]"
                    placeholder="(не указан)"
                  />
                </div>
                <div className="flex justify-between items-center mt-8 mb-4">
                  <Link
                    to="/password-change"
                    className="text-sm text-[#EB0000] hover:underline"
                  >
                    Изменить пароль
                  </Link>
                  <button
                    type="submit"
                    disabled={!isEditing || updateLoading}
                    className="bg-[#EB0000] text-white py-2 px-6 rounded hover:bg-[#eb0000a0] transition duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {updateLoading ? "Сохранение..." : "Сохранить"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>{" "}
      </main>
      <Modal
        isOpen={isModalOpen}
        onClose={closeModal}
        title={`Детали заказа #${selectedOrder?.pk}`}
      >
        {selectedOrder && <OrderDetailContent order={selectedOrder} />}
      </Modal>
      <Footer />
    </div>
  );
};

export default AccountPage;
