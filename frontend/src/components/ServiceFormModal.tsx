import React, {
  useState,
  useEffect,
  FormEvent,
  ChangeEvent,
  useRef,
} from "react";
import Modal from "./Modal";
import { Service } from "../interfaces";

interface ServiceFormData {
  name: string;
  description: string;
  price: string;
  duration_hours: string;
  photo?: File | null;
}

interface ServiceFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (formData: FormData, serviceId?: number) => Promise<void>; // Отправляем FormData
  initialData?: Service | null; // Для режима редактирования
}

type ServiceFormErrors = Record<string, string | undefined>;

const ServiceFormModal: React.FC<ServiceFormModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  initialData = null,
}) => {
  const [formData, setFormData] = useState<ServiceFormData>({
    name: "",
    description: "",
    price: "",
    duration_hours: "",
    photo: null,
  });
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<ServiceFormErrors>({}); // Ошибки валидации
  const fileInputRef = useRef<HTMLInputElement>(null); // Для сброса файла

  // Заполняем форму при открытии в режиме редактирования
  useEffect(() => {
    if (isOpen && initialData) {
      setFormData({
        name: initialData.name || "",
        description: initialData.description || "",
        price: initialData.price || "", // Цена из API может быть строкой
        duration_hours: initialData.duration_hours?.toString() || "",
        photo: undefined,
      });
      setPreviewUrl(initialData.photo_url || null); // Показываем текущее фото
      setErrors({}); // Сбрасываем ошибки
    } else if (isOpen && !initialData) {
      // Сбрасываем форму при открытии для создания
      setFormData({
        name: "",
        description: "",
        price: "",
        duration_hours: "",
        photo: null,
      });
      setPreviewUrl(null);
      setErrors({});
      // Сбрасываем значение input type="file"
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  }, [isOpen, initialData]);

  const handleChange = (
    e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[name]; // Удаляем ключ с ошибкой
        return newErrors;
      });
    }
    // Сбрасываем общую ошибку API
    if (errors.api) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors.api;
        return newErrors;
      });
    }
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setFormData((prev) => ({ ...prev, photo: file }));
      // Показываем превью нового изображения
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreviewUrl(reader.result as string);
      };
      reader.readAsDataURL(file);
      if (errors.photo) {
        setErrors((prev) => {
          const newErrors = { ...prev };
          delete newErrors.photo;
          return newErrors;
        });
      }
    } else {
      // Если файл отменен
      setFormData((prev) => ({ ...prev, photo: undefined }));
      setPreviewUrl(initialData?.photo_url || null); // Возвращаем старое превью
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrors({});

    // валидация
    const formErrors: Record<string, string> = {};
    if (!formData.name.trim()) formErrors.name = "Название обязательно.";
    if (isNaN(parseFloat(formData.price)) || parseFloat(formData.price) <= 0)
      formErrors.price = "Введите корректную положительную цену.";
    if (
      isNaN(parseInt(formData.duration_hours, 10)) ||
      parseInt(formData.duration_hours, 10) <= 0
    )
      formErrors.duration_hours =
        "Введите корректную положительную длительность.";

    if (Object.keys(formErrors).length > 0) {
      setErrors(formErrors); // ошибки фронтенда
      setLoading(false);
      return;
    }

    // FormData для отправки файла
    const submissionData = new FormData();
    submissionData.append("name", formData.name);
    submissionData.append("description", formData.description);
    submissionData.append("price", formData.price);
    submissionData.append("duration_hours", formData.duration_hours);
    // Добавляем файл, только если он был выбран
    if (formData.photo) {
      submissionData.append("photo", formData.photo);
    } else if (formData.photo === null && initialData?.photo) {
    }

    try {
      await onSubmit(submissionData, initialData?.pk);
      onClose(); // Закрываем окно после успешной отправки
    } catch (err: any) {
      console.error("Service form submission error:", err.response?.data);
      const errorData = err.response?.data;
      const apiErrors: ServiceFormErrors = {}; // новый тип
      let generalApiError = initialData
        ? "Ошибка обновления услуги."
        : "Ошибка создания услуги.";
      if (errorData) {
        // Распределяем ошибки по полям
        for (const key in errorData) {
          if (Array.isArray(errorData[key])) {
            apiErrors[key] = errorData[key].join(" ");
          } else if (typeof errorData[key] === "string") {
            apiErrors[key] = errorData[key];
          }
        }
        if (errorData.detail) {
          generalApiError = errorData.detail;
        }
      }
      apiErrors.api = generalApiError;
      setErrors(apiErrors);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={initialData ? "Редактировать услугу" : "Добавить новую услугу"}
    >
      <form onSubmit={handleSubmit}>
        {errors.api && (
          <p className="mb-4 text-center text-red-500 text-sm">{errors.api}</p>
        )}

        {/* Поля формы */}
        <div className="mb-4">
          <label
            htmlFor="name"
            className="block text-sm font-medium text-gray-300 mb-1"
          >
            Название*
          </label>
          <input
            type="text"
            id="name"
            name="name"
            value={formData.name}
            onChange={handleChange}
            required
            className={`w-full input-field ${errors.name ? "input-error" : ""}`}
          />
          {errors.name && (
            <p className="mt-1 text-xs text-red-500">{errors.name}</p>
          )}
        </div>

        <div className="mb-4">
          <label
            htmlFor="description"
            className="block text-sm font-medium text-gray-300 mb-1"
          >
            Описание
          </label>
          <textarea
            id="description"
            name="description"
            value={formData.description}
            onChange={handleChange}
            rows={4}
            className={`w-full input-field ${
              errors.description ? "input-error" : ""
            }`}
          ></textarea>
          {errors.description && (
            <p className="mt-1 text-xs text-red-500">{errors.description}</p>
          )}
        </div>

        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <label
              htmlFor="price"
              className="block text-sm font-medium text-gray-300 mb-1"
            >
              Цена (₽)*
            </label>
            <input
              type="number"
              step="0.01"
              min="0"
              id="price"
              name="price"
              value={formData.price}
              onChange={handleChange}
              required
              className={`w-full input-field ${
                errors.price ? "input-error" : ""
              }`}
            />
            {errors.price && (
              <p className="mt-1 text-xs text-red-500">{errors.price}</p>
            )}
          </div>
          <div>
            <label
              htmlFor="duration_hours"
              className="block text-sm font-medium text-gray-300 mb-1"
            >
              Длительность (ч)*
            </label>
            <input
              type="number"
              min="1"
              id="duration_hours"
              name="duration_hours"
              value={formData.duration_hours}
              onChange={handleChange}
              required
              className={`w-full input-field ${
                errors.duration_hours ? "input-error" : ""
              }`}
            />
            {errors.duration_hours && (
              <p className="mt-1 text-xs text-red-500">
                {errors.duration_hours}
              </p>
            )}
          </div>
        </div>

        <div className="mb-4">
          <label
            htmlFor="photo"
            className="block text-sm font-medium text-gray-300 mb-1"
          >
            Изображение
          </label>
          <input
            type="file"
            id="photo"
            name="photo"
            accept="image/*"
            onChange={handleFileChange}
            ref={fileInputRef}
            className={`w-full text-xs text-gray-400 file:mr-4 file:py-1 file:px-3 file:rounded file:border-0 file:text-xs file:font-semibold file:bg-[#EB0000] file:text-white hover:file:bg-[#eb0000b0] ${
              errors.photo ? "border border-red-500 rounded" : ""
            }`}
          />
          {errors.photo && (
            <p className="mt-1 text-xs text-red-500">{errors.photo}</p>
          )}
          {previewUrl && (
            <img
              src={previewUrl}
              alt="Превью"
              className="mt-2 h-24 w-auto rounded object-cover"
            />
          )}
        </div>

        {/* Кнопки */}
        <div className="mt-6 flex justify-end space-x-3">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-sm rounded bg-gray-600 hover:bg-gray-500 text-white"
          >
            Отмена
          </button>
          <button
            type="submit"
            disabled={loading}
            className="px-4 py-2 text-sm rounded bg-[#EB0000] hover:bg-[#eb0000a0] text-white disabled:opacity-50"
          >
            {loading
              ? initialData
                ? "Сохранение..."
                : "Добавление..."
              : initialData
              ? "Сохранить изменения"
              : "Добавить услугу"}
          </button>
        </div>
      </form>
    </Modal>
  );
};

export default ServiceFormModal;
