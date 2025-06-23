export interface News {
  pk: number;
  title: string;
  content: string;
  published_at: string;
  author: UserSummary | null; // Автор может быть null
  pdf_file: string | null;
  pdf_file_url: string | null; // Абсолютный URL для скачивания
}
// Интерфейс для элемента корзины
export interface CartItem {
  pk: number;
  service: {
    pk: number;
    name: string;
    price: string;
    photo_url?: string | null;
  };
  quantity: number;
  added_at: string;
  total_cost: string;
}

// Интерфейс для корзины
export interface Cart {
  pk: number;
  user: UserSummary;
  items: CartItem[];
  created_at: string;
  updated_at: string;
  total_cost: string;
  total_items_count: number;
  total_positions_count: number;
}

export interface OrderStatus {
  pk: number;
  status_name: string;
  display_name: string;
}

export interface Order {
  pk: number;
  client: UserSummary | null; // Может быть null, если пользователь удален
  executor: {
    /* ExecutorSummary */ pk: number;
    user: UserSummary;
    specialization: string;
  } | null;
  service: {
    /* ServiceSummary */ pk: number;
    name: string;
    price: string;
  } | null;
  status: OrderStatus | null;
  created_at: string;
  scheduled_at: string;
  completed_at: string | null;
}

export interface UserSummary {
  pk: number;
  username: string;
  full_name: string;
  avatar_url: string | null;
}

// полный интерфейс User
export interface UserProfile extends UserSummary {
  email: string;
  first_name: string;
  last_name: string;
  phone_number: string | null;
  date_joined: string;
  last_login: string | null;
  avatar: string | null;
  is_staff: boolean;
  is_executor: boolean;
}

export interface Service {
  pk: number;
  name: string;
  description: string;
  price: string;
  duration_hours: number;
  photo: string | null;
  photo_url: string | null;
  created_at: string;
}

export interface ExecutorSummary {
  pk: number;
  user: UserSummary;
  specialization: string;
}

export interface PortfolioItem {
  pk: number;
  executor: ExecutorSummary;
  title: string;
  image: string | null;
  image_url: string | null;
  video_link: string | null;
  description: string;
  uploaded_at: string;
}

export interface Review {
  pk: number;
  user_read: UserSummary;
  executor_read: ExecutorSummary;
  order_read: number | null;
  rating: number;
  comment: string;
  created_at: string;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface Exam {
  pk: number;
  name: string;
  created_at: string;
  exam_date: string;
  image_url: string | null;
  students: UserSummary[];
  is_public: boolean;
}