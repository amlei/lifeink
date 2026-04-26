import { useState, useEffect, useRef, useCallback } from "react";
import { X, User, Settings, Database, FileText, Loader2, RefreshCw } from "lucide-react";
import type { UserProfile } from "../types";
import {
  checkBinding,
  startBinding,
  unbind as unbindApi,
  refreshProfile,
  connectBindWs,
} from "../api/bind";
import type { PlatformProfile, PollResult } from "../community/types/bind";

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

  // Douban binding state
  const [doubanBound, setDoubanBound] = useState(false);
  const [doubanProfile, setDoubanProfile] = useState<PlatformProfile | null>(null);
  const [binding, setBinding] = useState(false);
  const [bindPhase, setBindPhase] = useState<PollResult["status"]>("idle");
  const [qrSrc, setQrSrc] = useState<string | null>(null);
  const [bindError, setBindError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  // Check binding on mount
  useEffect(() => {
    checkBinding("douban").then((data) => {
      if (data.bound) {
        setDoubanBound(true);
        setDoubanProfile(data.profile ?? null);
      }
    });
  }, []);

  const closeWs = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  const handleBind = async () => {
    setBinding(true);
    setBindError(null);
    setQrSrc(null);
    try {
      await startBinding("douban");

      wsRef.current = connectBindWs("douban", {
        onQr: (base64) => setQrSrc(`data:image/png;base64,${base64}`),
        onStatus: (status) => {
          setBindPhase(status);
          if (status === "scanned") setQrSrc(null);
        },
        onBound: (_userId, profile) => {
          setDoubanBound(true);
          setDoubanProfile(profile ?? null);
          setBinding(false);
          setQrSrc(null);
        },
        onFailed: (error) => {
          setBindError(error);
          setBinding(false);
          setQrSrc(null);
        },
      });
    } catch {
      setBindError("启动绑定失败");
      setBinding(false);
    }
  };

  const handleUnbind = async () => {
    await unbindApi("douban");
    setDoubanBound(false);
    setDoubanProfile(null);
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      const data = await refreshProfile("douban");
      if (data.profile) {
        setDoubanProfile(data.profile);
      }
    } catch {
      /* ignore */
    }
    setRefreshing(false);
  };

  // Cleanup WebSocket on unmount
  useEffect(() => () => closeWs(), [closeWs]);

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
                    {activePlatform === "douban" && (
                      <div className="platform-binding-card">
                        <div className="platform-binding-row">
                          <div className="platform-info">
                            <img
                              src="/douban.svg"
                              alt="豆瓣"
                              className="platform-icon"
                            />
                            <div className="platform-detail">
                              <span className="platform-name">豆瓣</span>
                              {doubanBound && doubanProfile && (
                                <span className="platform-status">
                                  已绑定 ({doubanProfile.name ?? doubanProfile.user_id})
                                </span>
                              )}
                            </div>
                          </div>
                          {doubanBound ? (
                            <div className="platform-actions">
                              <button
                                className="platform-bind-btn"
                                onClick={handleRefresh}
                                disabled={refreshing}
                              >
                                {refreshing ? (
                                  <>
                                    <Loader2 size={14} className="spin" />
                                    更新中
                                  </>
                                ) : (
                                  <>
                                    <RefreshCw size={14} />
                                    更新信息
                                  </>
                                )}
                              </button>
                              <button className="platform-bind-btn unbind" onClick={handleUnbind}>
                                解绑
                              </button>
                            </div>
                          ) : (
                            <button
                              className="platform-bind-btn"
                              onClick={handleBind}
                              disabled={binding}
                            >
                              {binding ? (
                                <>
                                  <Loader2 size={14} className="spin" />
                                  {bindPhase === "pending" && "等待扫码"}
                                  {bindPhase === "scanned" && "扫码成功，请在手机确认"}
                                  {bindPhase === "logged_in" && "登录成功"}
                                  {bindPhase === "fetching_profile" && "正在获取用户资料"}
                                </>
                              ) : (
                                "绑定"
                              )}
                            </button>
                          )}
                        </div>
                        {doubanBound && doubanProfile && (
                          <div className="platform-profile-detail">
                            {doubanProfile.avatar && (
                              <img className="profile-detail-avatar" src={doubanProfile.avatar} alt="" />
                            )}
                            <div className="profile-detail-grid">
                              {doubanProfile.name && (
                                <div className="profile-field">
                                  <label>昵称</label>
                                  <span>{doubanProfile.name}</span>
                                </div>
                              )}
                              {doubanProfile.signature && (
                                <div className="profile-field">
                                  <label>签名</label>
                                  <span>{doubanProfile.signature}</span>
                                </div>
                              )}
                              {doubanProfile.location && (
                                <div className="profile-field">
                                  <label>IP属地</label>
                                  <span>{doubanProfile.location}</span>
                                </div>
                              )}
                              {doubanProfile.join_date && (
                                <div className="profile-field">
                                  <label>加入时间</label>
                                  <span>{doubanProfile.join_date}</span>
                                </div>
                              )}
                              {doubanProfile.bio && (
                                <div className="profile-field" style={{ gridColumn: "1 / -1" }}>
                                  <label>简介</label>
                                  <span>{doubanProfile.bio}</span>
                                </div>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                    {activePlatform !== "douban" &&
                      (() => {
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
                            <button className="platform-bind-btn" disabled>
                              即将支持
                            </button>
                          </div>
                        );
                      })()}
                    {qrSrc && (
                      <div className="qr-overlay">
                        <div className="qr-card">
                          <img src={qrSrc} alt="QR Code" className="qr-image" />
                          <p>使用豆瓣 App 扫码登录</p>
                        </div>
                      </div>
                    )}
                    {bindError && (
                      <p className="bind-error">{bindError}</p>
                    )}
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
