export interface PlatformProfile {
  user_id: string;
  name: string | null;
  avatar: string | null;
  signature: string | null;
  bio: string | null;
  join_date: string | null;
  location: string | null;
}

export interface BindStatus {
  bound: boolean;
  user_id?: string;
  profile?: PlatformProfile;
}

export interface PollResult {
  status: "idle" | "pending" | "scanned" | "logged_in" | "fetching_profile" | "scraping" | "bound" | "failed";
  qr_base64?: string;
  user_id?: string;
  profile?: PlatformProfile;
  scrape_phase?: "books" | "movies" | "done";
  scrape_counts?: Record<string, number>;
  error?: string;
}

export interface BookItem {
  title: string;
  url: string;
  cover: string | null;
  author: string | null;
  country: string | null;
  translator: string | null;
  publisher: string | null;
  pub_date: string | null;
  price: string | null;
  rating: number | null;
  read_date: string | null;
  status: string | null;
  tags: string[] | null;
  comment: string | null;
}

export interface MovieItem {
  title: string;
  url: string;
  cover: string | null;
  release_date: string | null;
  rating: number | null;
  watch_date: string | null;
  tags: string[] | null;
  comment: string | null;
}

export interface NoteItem {
  title: string;
  url: string | null;
  date: string | null;
  location: string | null;
  body: string | null;
}

export interface CommunityData {
  books: BookItem[];
  movies: MovieItem[];
  notes: NoteItem[];
}
