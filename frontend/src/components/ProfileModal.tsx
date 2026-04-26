import { useState } from "react";
import { X, User, Settings, Database, FileText } from "lucide-react";
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

const platforms = [
  { id: "douban", label: "豆瓣", icon: "/douban.svg", rounded: false },
  { id: "flomo", label: "flomo", icon: "/flomoapp.svg", rounded: false },
  { id: "weread", label: "微信读书", icon: "/weread.webp", rounded: true },
] as const;

export function ProfileModal({ user, onClose }: ProfileModalProps) {
  const [activeTab, setActiveTab] = useState<string>("general");
  const [activePlatform, setActivePlatform] = useState<string>("douban");

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>设置</h2>
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
                <h3>通用设置</h3>
                <p className="settings-desc">应用偏好和显示选项。</p>
              </div>
            )}
            {activeTab === "account" && (
              <div className="settings-page">
                <h3>帐号管理</h3>
                <div className="settings-profile">
                  <div className="profile-avatar-lg">
                    <User size={40} />
                  </div>
                  <div className="profile-grid">
                    <div className="profile-field">
                      <label>用户名</label>
                      <span>{user.name}</span>
                    </div>
                    <div className="profile-field">
                      <label>邮箱</label>
                      <span>{user.email}</span>
                    </div>
                    <div className="profile-field">
                      <strong>{user.booksRead}</strong>
                      <span>已读图书</span>
                    </div>
                    <div className="profile-field">
                      <strong>{user.moviesWatched}</strong>
                      <span>已看电影</span>
                    </div>
                  </div>
                </div>
                <div className="platform-section">
                  <h4>第三方平台绑定</h4>
                  <div className="platform-tabs">
                    {platforms.map((p) => (
                      <button
                        key={p.id}
                        className={`platform-tab ${activePlatform === p.id ? "active" : ""}`}
                        onClick={() => setActivePlatform(p.id)}
                      >
                        <img
                          src={p.icon}
                          alt={p.label}
                          className={`platform-icon ${p.rounded ? "rounded" : ""}`}
                        />
                        <span>{p.label}</span>
                      </button>
                    ))}
                  </div>
                  <div className="platform-panel">
                    {(() => {
                      const p = platforms.find((x) => x.id === activePlatform)!;
                      return (
                        <div className="platform-binding">
                          <div className="platform-info">
                            <img
                              src={p.icon}
                              alt={p.label}
                              className={`platform-icon ${p.rounded ? "rounded" : ""}`}
                            />
                            <span className="platform-name">{p.label}</span>
                          </div>
                          <button className="platform-bind-btn">绑定</button>
                        </div>
                      );
                    })()}
                  </div>
                </div>
              </div>
            )}
            {activeTab === "data" && (
              <div className="settings-page">
                <h3>数据管理</h3>
                <p className="settings-desc">管理从豆瓣同步的数据。</p>
              </div>
            )}
            {activeTab === "terms" && (
              <div className="settings-page">
                <h3>服务协议</h3>
                <p className="settings-desc">服务条款与隐私政策。</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
