import { User, X } from "lucide-react";
import type { UserProfile } from "../types";

interface ProfileModalProps {
  user: UserProfile;
  onClose: () => void;
}

export function ProfileModal({ user, onClose }: ProfileModalProps) {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Profile</h2>
          <button className="modal-close" onClick={onClose}>
            <X size={18} />
          </button>
        </div>
        <div className="modal-body">
          <div className="profile-avatar-lg">
            <User size={32} />
          </div>
          <div className="profile-field">
            <label>Name</label>
            <span>{user.name}</span>
          </div>
          <div className="profile-field">
            <label>Email</label>
            <span>{user.email}</span>
          </div>
          <div className="profile-field">
            <label>Douban ID</label>
            <span>{user.doubanId}</span>
          </div>
          <div className="profile-stats">
            <div className="profile-stat">
              <strong>{user.booksRead}</strong>
              <span>Books</span>
            </div>
            <div className="profile-stat">
              <strong>{user.moviesWatched}</strong>
              <span>Movies</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
