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
  status: "idle" | "pending" | "scanned" | "logged_in" | "fetching_profile" | "bound" | "failed";
  qr_base64?: string;
  user_id?: string;
  profile?: PlatformProfile;
  error?: string;
}
