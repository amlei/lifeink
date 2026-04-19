import {
  PanelRightClose,
  Plus,
  User,
  Settings,
  LogIn,
} from "lucide-react";
import type { ChatMeta, UserProfile } from "../types";

interface SidebarProps {
  open: boolean;
  chats: ChatMeta[];
  activeChatId: string | null;
  user: UserProfile | null;
  onToggle: () => void;
  onSelectChat: (id: string) => void;
  onNewChat: () => void;
  onShowProfile: () => void;
}

export function Sidebar({
  open,
  chats,
  activeChatId,
  user,
  onToggle,
  onSelectChat,
  onNewChat,
  onShowProfile,
}: SidebarProps) {
  if (!open) return null;

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <span className="sidebar-title">History</span>
        <button className="sidebar-toggle" onClick={onToggle}>
          <PanelRightClose size={16} />
        </button>
      </div>

      <button className="new-chat-btn" onClick={onNewChat}>
        <Plus size={15} />
        New Chat
      </button>

      <div className="sidebar-list">
        {chats.map((chat) => (
          <div
            key={chat.id}
            className={`chat-item ${activeChatId === chat.id ? "active" : ""}`}
            onClick={() => onSelectChat(chat.id)}
          >
            {chat.title}
          </div>
        ))}
      </div>

      <div className="sidebar-footer">
        {user ? (
          <div className="user-info" onClick={onShowProfile}>
            <div className="user-avatar">
              <User size={16} />
            </div>
            <span className="user-name">{user.name}</span>
            <Settings size={14} className="user-settings-icon" />
          </div>
        ) : (
          <div className="user-info user-login" onClick={onShowProfile}>
            <LogIn size={16} />
            <span>Login</span>
          </div>
        )}
      </div>
    </aside>
  );
}
