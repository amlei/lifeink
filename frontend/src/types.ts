export interface ChatMeta {
  id: string;
  title: string;
  createdAt: number;
}

export interface UserProfile {
  name: string;
  avatar: string;
  email: string;
  doubanId: string;
  booksRead: number;
  moviesWatched: number;
}
