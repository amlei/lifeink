import { useState } from "react";
import { X, User, Settings, Shield, Database, FileText } from "lucide-react";
import type { UserProfile } from "../types";

interface ProfileModalProps {
  user: UserProfile;
  onClose: () => void;
}

const tabs = [
  { id: "general", label: "通用设置", icon: Settings },
  { id: "account", label: "帐号管理", icon: User },
  { id: "data", label: "数据管理", icon: Database },
  { id: "terms", label: "服务协议", icon: FileText },
] as const;

export function ProfileModal({ user, onClose }: ProfileModalProps) {
  const [activeTab, setActiveTab] = useState<string>("general");

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Settings</h2>
          <button className="modal-close" onClick={onClose}>
            <X size={22} />
          </button>
        </div>
        <div className="settings-layout">
          <nav className="settings-tabs">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  className={`settings-tab ${activeTab === tab.id ? "active" : ""}`}
                  onClick={() => setActiveTab(tab.id)}
                >
                  <Icon size={20} />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </nav>
          <div className="settings-content">
            {activeTab === "general" && (
              <div className="settings-page">
                <h3>General Settings</h3>
                <p className="settings-desc">App preferences and display options.</p>
              </div>
            )}
            {activeTab === "account" && (
              <div className="settings-page">
                <h3>Account</h3>
                <div className="settings-profile">
                  <div className="profile-avatar-lg">
                    <User size={40} />
                  </div>
                  <div className="profile-fields">
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
                  </div>
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
            )}
            {activeTab === "data" && (
              <div className="settings-page">
                <h3>Data Management</h3>
                <p className="settings-desc">Manage your synced data from Douban.</p>
              </div>
            )}
            {activeTab === "terms" && (
              <div className="settings-page">
                <h3>Terms of Service</h3>
                <p className="settings-desc">Service agreement and privacy policy.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
