import React, {
  useState,
  useEffect,
  FormEvent,
  ChangeEvent,
  useRef,
} from "react";
import Modal from "./Modal";
import { PortfolioItem } from "../interfaces";

interface PortfolioFormData {
  title: string;
  description: string;
  video_link: string; // Может быть пустым
  image?: File | null;
}

interface PortfolioFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (formData: FormData, itemId?: number) => Promise<void>; // Отправляем FormData
  initialData?: PortfolioItem | null; // Для режима редактирования
}

type PortfolioFormErrors = Record<string, string | undefined>;

const PortfolioFormModal: React.FC<PortfolioFormModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  initialData = null,
}) => {
  const [formData, setFormData] = useState<PortfolioFormData>({
    title: "",
    description: "",
    video_link: "",
    image: null,
  });
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<PortfolioFormErrors>({}); // новый тип
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Заполнение формы
  useEffect(() => {
    if (isOpen && initialData) {
      setFormData({
        title: initialData.title || "",
        description: initialData.description || "",
        video_link: initialData.video_link || "",
        image: undefined,
      });
      setPreviewUrl(initialData.image_url || null);
      setErrors({});
    } else if (isOpen && !initialData) {
      // Сброс
      setFormData({ title: "", description: "", video_link: "", image: null });
      setPreviewUrl(null);
      setErrors({});
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
        const n = { ...prev };
        delete n[name];
        return n;
      });
    }
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setFormData((prev) => ({ ...prev, image: file }));
      const reader = new FileReader();
      reader.onloadend = () => setPreviewUrl(reader.result as string);
      reader.readAsDataURL(file);
      if (errors.image) {
        setErrors((prev) => {
          const n = { ...prev };
          delete n.image;
          return n;
        });
      }
    } else {
      setFormData((prev) => ({ ...prev, image: undefined }));
      setPreviewUrl(initialData?.image_url || null);
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrors({});

    const formErrors: Record<string, string> = {};
    if (!formData.title.trim()) formErrors.title = "Название обязательно.";

    if (Object.keys(formErrors).length > 0) {
      setErrors(formErrors);
      setLoading(false);
      return;
    }

    const submissionData = new FormData();
    submissionData.append("title", formData.title);
    submissionData.append("description", formData.description);
    submissionData.append("video_link", formData.video_link);
    if (formData.image) {
      submissionData.append("image", formData.image);
    } else if (formData.image === null && initialData?.image) {
    }

    try {
      await onSubmit(submissionData, initialData?.pk);
      onClose();
    } catch (err: any) {
      // обработка ошибок API, установка errors
      const errorData = err.response?.data;
      const apiErrors: PortfolioFormErrors = {}; // Используем новый тип
      let generalApiError = initialData
        ? "Ошибка обновления работы."
        : "Ошибка добавления работы.";
      if (errorData) apiErrors.api = generalApiError;
      setErrors(apiErrors);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={
        initialData ? "Редактировать работу" : "Добавить работу в портфолио"
      }
    >
      <form onSubmit={handleSubmit}>
        {errors.api && (
          <p className="mb-4 text-center text-red-500 text-sm">{errors.api}</p>
        )}

        {/* Поля формы: Title, Description, Video Link, Image */}
        <div className="mb-4">
          <label
            htmlFor="title"
            className="block text-sm font-medium text-gray-300 mb-1"
          >
            Название*
          </label>
          <input
            type="text"
            id="title"
            name="title"
            value={formData.title}
            onChange={handleChange}
            required
            className={`w-full input-field ${
              errors.title ? "input-error" : ""
            }`}
          />
          {errors.title && (
            <p className="mt-1 text-xs text-red-500">{errors.title}</p>
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
            rows={5}
            className={`w-full input-field ${
              errors.description ? "input-error" : ""
            }`}
          ></textarea>
          {errors.description && (
            <p className="mt-1 text-xs text-red-500">{errors.description}</p>
          )}
        </div>

        <div className="mb-4">
          <label
            htmlFor="video_link"
            className="block text-sm font-medium text-gray-300 mb-1"
          >
            Ссылка на видео/проект
          </label>
          <input
            type="url"
            id="video_link"
            name="video_link"
            value={formData.video_link}
            onChange={handleChange}
            placeholder="https://..."
            className={`w-full input-field ${
              errors.video_link ? "input-error" : ""
            }`}
          />
          {errors.video_link && (
            <p className="mt-1 text-xs text-red-500">{errors.video_link}</p>
          )}
        </div>

        <div className="mb-4">
          <label
            htmlFor="image"
            className="block text-sm font-medium text-gray-300 mb-1"
          >
            Изображение
          </label>
          <input
            type="file"
            id="image"
            name="image"
            accept="image/*"
            onChange={handleFileChange}
            ref={fileInputRef}
            className={`w-full text-xs text-gray-400 file:mr-4 file:py-1 file:px-3 file:rounded file:border-0 file:text-xs file:font-semibold file:bg-[#EB0000] file:text-white hover:file:bg-[#eb0000b0] ${
              errors.image ? "border border-red-500 rounded" : ""
            }`}
          />
          {errors.image && (
            <p className="mt-1 text-xs text-red-500">{errors.image}</p>
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
              : "Добавить портфолио"}
          </button>
        </div>
      </form>
    </Modal>
  );
};

export default PortfolioFormModal;
