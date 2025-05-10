import React from 'react';
import { useAuth } from '../context/AuthContext';

const NotificationCenter: React.FC = () => {
  const { notifications, removeNotification } = useAuth();

  if (notifications.length === 0) {
    return null;
  }

  return (
    // Контейнер для уведомлений 
    <div className="fixed bottom-4 right-4 z-[100] space-y-3 w-full max-w-sm">
      {notifications.map((notification) => (
        <div
          key={notification.id}
          className={`relative p-4 rounded-md shadow-lg flex items-start justify-between transition-all duration-300 ease-in-out transform animate-fade-in-up ${
            notification.type === 'success'
              ? 'bg-green-600 border border-green-700 text-white'
              : 'bg-red-600 border border-red-700 text-white'
          }`}
        >
          {/* Иконка  */}
          <div className="flex-shrink-0 mr-3">
             {notification.type === 'success' ? (
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" /></svg>
             ) : (
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" /></svg>
             )}
          </div>
          {/* Текст сообщения */}
          <div className="flex-grow text-sm">{notification.message}</div>
          {/* Кнопка закрытия */}
          <button
            onClick={() => removeNotification(notification.id)}
            className="ml-3 text-current opacity-70 hover:opacity-100 flex-shrink-0"
            aria-label="Закрыть уведомление"
          >
             <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd"></path></svg>
          </button>
        </div>
      ))}
    </div>
  );
};

export default NotificationCenter;