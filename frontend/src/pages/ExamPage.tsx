import React, { useState, useEffect } from "react";
import axios from "axios";
import Header from "../components/Header";
import Footer from "../components/Footer";
import { Exam } from "../interfaces";

const ExamPage: React.FC = () => {
  const [exams, setExams] = useState<Exam[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchExams = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await axios.get<{ results: Exam[] }>(
          "/studio/api/azexam/"
        );
        setExams(response.data.results);
      } catch (err: any) {
        setError("Не удалось загрузить данные об экзаменах.");
        console.error("Error fetching exams:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchExams();
  }, []);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString("ru-RU", {
      day: "2-digit",
      month: "long",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div className="bg-[#0D0C0C] text-gray-100 min-h-screen flex flex-col">
      <Header />
      <main className="flex-grow container mx-auto px-4 py-8 md:py-12">
        <div className="text-center mb-10">
          <h1 className="text-3xl font-bold text-white mb-2">
            Страница контрольного задания
          </h1>
          <p className="text-gray-400">
            Заводун Александр, группа 231-323
          </p>
        </div>

        {loading && (
          <p className="text-center text-gray-400">Загрузка экзаменов...</p>
        )}
        {error && <p className="text-center text-red-500">{error}</p>}
        
        {!loading && !error && exams.length === 0 && (
           <p className="text-center text-gray-400 bg-[#181818] p-8 rounded-lg">
             Опубликованных экзаменов пока нет.
           </p>
        )}

        <div className="space-y-6">
          {exams.map((exam) => (
            <article
              key={exam.pk}
              className="bg-[#181818] p-6 rounded-lg shadow-xl border border-gray-800"
            >
              {/* 1. Название экзамена */}
              <h2 className="text-2xl font-bold text-white mb-3">
                {exam.name}
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Левая колонка с изображением */}
                <div className="md:col-span-1">
                  {/* 4. Изображение */}
                  {exam.image_url ? (
                    <img
                      src={exam.image_url}
                      alt={`Задание к экзамену: ${exam.name}`}
                      className="w-full h-auto object-cover rounded-md border border-gray-700"
                    />
                  ) : (
                    <div className="w-full h-48 flex items-center justify-center bg-gray-700 rounded-md text-gray-500">
                      Нет изображения
                    </div>
                  )}
                </div>

                {/* Правая колонка с информацией */}
                <div className="md:col-span-2 space-y-4 text-sm">
                  <div>
                    <p className="text-gray-400 font-semibold">Дата проведения:</p>
                    {/* 3. Дата проведения */}
                    <p className="text-white">{formatDate(exam.exam_date)}</p>
                  </div>
                  <div>
                    <p className="text-gray-400 font-semibold">Студенты:</p>
                    {/* 5. Студенты */}
                    {exam.students.length > 0 ? (
                      <ul className="list-disc list-inside text-white">
                        {exam.students.map((student) => (
                          <li key={student.pk}>
                            {student.full_name || student.username}
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-gray-500 italic">Студенты не назначены</p>
                    )}
                  </div>
                   <div>
                    <p className="text-gray-400 font-semibold">Дата создания записи:</p>
                    {/* 2. Дата создания */}
                    <p className="text-white">{formatDate(exam.created_at)}</p>
                  </div>
                </div>
              </div>
            </article>
          ))}
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default ExamPage;