import React, {
  useState,
  useEffect,
  FormEvent,
  ChangeEvent,
  useRef,
} from "react";
import Modal from "./Modal";
import { News } from "../interfaces";

interface NewsFormData {
  title: string;
  content: string;
  pdf_file?: File | null;
}

type NewsFormErrors = Record<string, string | undefined>;

interface NewsFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (formData: FormData, newsId?: number) => Promise<void>;
  initialData?: News | null;
}

const NewsFormModal: React.FC<NewsFormModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  initialData = null,
}) => {
  const [formData, setFormData] = useState<NewsFormData>({
    title: "",
    content: "",
    pdf_file: null,
  });
  const [previewPdfName, setPreviewPdfName] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<NewsFormErrors>({});
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isOpen && initialData) {
      setFormData({
        title: initialData.title || "",
        content: initialData.content || "",
        pdf_file: undefined,
      });
      setPreviewPdfName(
        initialData.pdf_file_url
          ? initialData.pdf_file_url.split("/").pop() || "файл прикреплен"
          : null
      );
      setErrors({});
    } else if (isOpen && !initialData) {
      setFormData({ title: "", content: "", pdf_file: null });
      setPreviewPdfName(null);
      setErrors({});
      if (fileInputRef.current) fileInputRef.current.value = "";
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
    if (errors.api) {
      setErrors((prev) => {
        const n = { ...prev };
        delete n.api;
        return n;
      });
    }
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setFormData((prev) => ({ ...prev, pdf_file: file }));
      setPreviewPdfName(file.name);
      if (errors.pdf_file) {
        setErrors((prev) => {
          const n = { ...prev };
          delete n.pdf_file;
          return n;
        });
      }
    } else {
      setFormData((prev) => ({ ...prev, pdf_file: undefined }));
      setPreviewPdfName(
        initialData?.pdf_file_url
          ? initialData.pdf_file_url.split("/").pop() || "файл прикреплен"
          : null
      );
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrors({});
    const formErrors: NewsFormErrors = {};
    if (!formData.title.trim()) formErrors.title = "Заголовок обязатеlen.";
    if (!formData.content.trim())
      formErrors.content = "Содержимое обязательно.";
    if (Object.keys(formErrors).length > 0) {
      setErrors(formErrors);
      setLoading(false);
      return;
    }

    const submissionData = new FormData();
    submissionData.append("title", formData.title);
    submissionData.append("content", formData.content);
    if (formData.pdf_file) {
      submissionData.append("pdf_file", formData.pdf_file);
    } else if (formData.pdf_file === null && initialData?.pdf_file) {
    }

    try {
      await onSubmit(submissionData, initialData?.pk);
      onClose();
    } catch (err: any) {
      const errorData = err.response?.data;
      const apiErrors: NewsFormErrors = {};
      let generalApiError = initialData
        ? "Ошибка обновления новости."
        : "Ошибка добавления новости.";
      if (errorData) {
        for (const key in errorData) {
          if (key === "detail") generalApiError = errorData.detail;
          else if (Array.isArray(errorData[key]))
            apiErrors[key as keyof NewsFormErrors] = errorData[key].join(" ");
          else if (typeof errorData[key] === "string")
            apiErrors[key as keyof NewsFormErrors] = errorData[key];
        }
        if (
          Object.keys(apiErrors).length > 0 &&
          generalApiError ===
            (initialData
              ? "Ошибка обновления новости."
              : "Ошибка добавления новости.")
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
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={initialData ? "Редактировать новость" : "Добавить новость"}
    >
      <form onSubmit={handleSubmit}>
        {errors.api && (
          <p className="mb-4 text-center text-red-500 text-sm">{errors.api}</p>
        )}

        {/* Заголовок */}
        <div className="mb-4">
          <label
            htmlFor="title-news"
            className="block text-sm font-medium text-gray-300 mb-1"
          >
            Заголовок*
          </label>
          <input
            type="text"
            id="title-news"
            name="title"
            value={formData.title}
            onChange={handleChange}
            required
            className={`w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-[#EB0000] ${
              errors.title ? "border-red-500" : "border-gray-600"
            }`}
          />
          {errors.title && (
            <p className="mt-1 text-xs text-red-500">{errors.title}</p>
          )}
        </div>

        {/* Содержимое */}
        <div className="mb-4">
          <label
            htmlFor="content-news"
            className="block text-sm font-medium text-gray-300 mb-1"
          >
            Содержимое* (поддерживает Markdown)
          </label>
          <textarea
            id="content-news"
            name="content"
            value={formData.content}
            onChange={handleChange}
            rows={10}
            required
            className={`w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-[#EB0000] ${
              errors.content ? "border-red-500" : "border-gray-600"
            }`}
          />
          {errors.content && (
            <p className="mt-1 text-xs text-red-500">{errors.content}</p>
          )}
        </div>

        {/* PDF Файл */}
        <div className="mb-6">
          <label
            htmlFor="pdf_file-news"
            className="block text-sm font-medium text-gray-300 mb-1"
          >
            PDF файл (необязательно)
          </label>
          <input
            type="file"
            id="pdf_file-news"
            name="pdf_file"
            accept=".pdf"
            onChange={handleFileChange}
            ref={fileInputRef}
            className={`w-full text-xs text-gray-400 file:mr-4 file:py-1.5 file:px-4 file:rounded file:border-0 file:text-xs file:font-semibold file:bg-[#EB0000] file:text-white hover:file:bg-[#eb0000b0] cursor-pointer ${
              errors.pdf_file ? "border border-red-500 rounded" : ""
            }`}
          />
          {previewPdfName && (
            <p className="mt-1 text-xs text-gray-400">
              Выбран файл: {previewPdfName}
            </p>
          )}
          {errors.pdf_file && (
            <p className="mt-1 text-xs text-red-500">{errors.pdf_file}</p>
          )}
        </div>

        {/* Кнопки */}
        <div className="mt-6 flex justify-end space-x-3">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-sm rounded bg-gray-600 hover:bg-gray-500 text-white transition-colors"
          >
            Отмена
          </button>
          <button
            type="submit"
            disabled={loading}
            className="px-4 py-2 text-sm rounded bg-[#EB0000] hover:bg-[#eb0000a0] text-white disabled:opacity-50 transition-colors"
          >
            {loading
              ? initialData
                ? "Сохранение..."
                : "Добавление..."
              : initialData
              ? "Сохранить изменения"
              : "Добавить новость"}
          </button>
        </div>
      </form>
    </Modal>
  );
};

export default NewsFormModal;
