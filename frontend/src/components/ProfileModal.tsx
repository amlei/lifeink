import { useState, useEffect, useRef, useCallback } from "react";
import "./ProfileModal.css";
import { X, User, Settings, Database, FileText, Loader2, RefreshCw, ChevronDown, Pencil, Check, KeyRound } from "lucide-react";
import { useAuth } from "../contexts/AuthContext";
import { getPasswordStrength } from "../utils/password";
import type { StrengthLevel } from "../utils/password";
import { updateProfile, changePassword } from "../api/auth";
import {
  checkBinding,
  startBinding,
  unbind as unbindApi,
  refreshProfile,
  syncData,
  connectBindWs,
  getCommunityData,
} from "../api/douban";
import type { PlatformProfile, PollResult, BookItem, MovieItem, NoteItem } from "../types/douban";
import { AuthModal } from "./AuthModal";

interface ProfileModalProps {
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

const STRENGTH_COLORS: Record<StrengthLevel, [string, string, string]> = {
  0: ["var(--border)", "var(--border)", "var(--border)"],
  1: ["#ef4444", "var(--border)", "var(--border)"],
  2: ["#f59e0b", "#f59e0b", "var(--border)"],
  3: ["#22c55e", "#22c55e", "#22c55e"],
};

const STRENGTH_LABELS: Record<StrengthLevel, string> = {
  0: "",
  1: "弱",
  2: "中",
  3: "强",
};

function StrengthBar({ level }: { level: StrengthLevel }) {
  const colors = STRENGTH_COLORS[level];
  return (
    <div className="pw-strength">
      <div className="pw-strength-bars">
        {colors.map((color, i) => (
          <div key={i} className="pw-strength-seg" style={{ backgroundColor: color }} />
        ))}
      </div>
      {level > 0 && <span className="pw-strength-label">{STRENGTH_LABELS[level]}</span>}
    </div>
  );
}

export function ProfileModal({ onClose }: ProfileModalProps) {
  const { user, logout, refreshUser } = useAuth();

  // Settings state (only used when logged in)
  const [activeTab, setActiveTab] = useState<string>("general");
  const [activePlatform, setActivePlatform] = useState<string>("douban");
  const [doubanBound, setDoubanBound] = useState(false);
  const [doubanProfile, setDoubanProfile] = useState<PlatformProfile | null>(null);
  const [binding, setBinding] = useState(false);
  const [bindPhase, setBindPhase] = useState<PollResult["status"]>("idle");
  const [qrSrc, setQrSrc] = useState<string | null>(null);
  const [bindError, setBindError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [syncPhase, setSyncPhase] = useState<PollResult["scrape_phase"]>(undefined);
  const [scrapePhase, setScrapePhase] = useState<PollResult["scrape_phase"]>(undefined);
  const [scrapeCounts, setScrapeCounts] = useState<Record<string, number>>({});
  const [menuOpen, setMenuOpen] = useState(false);
  const [editingProfile, setEditingProfile] = useState(false);
  const [editName, setEditName] = useState("");
  const [editBio, setEditBio] = useState("");
  const [editAvatar, setEditAvatar] = useState<string | null>(null);
  const [profileSaving, setProfileSaving] = useState(false);
  const [profileError, setProfileError] = useState<string | null>(null);
  const [showChangePw, setShowChangePw] = useState(false);
  const [oldPw, setOldPw] = useState("");
  const [newPw, setNewPw] = useState("");
  const [pwError, setPwError] = useState<string | null>(null);
  const [pwSaving, setPwSaving] = useState(false);
  const [books, setBooks] = useState<BookItem[]>([]);
  const [movies, setMovies] = useState<MovieItem[]>([]);
  const [notes, setNotes] = useState<NoteItem[]>([]);
  const [dataTab, setDataTab] = useState<"books" | "movies" | "notes">("books");
  const wsRef = useRef<WebSocket | null>(null);
  const menuRef = useRef<HTMLDivElement | null>(null);

  // Check binding on mount
  useEffect(() => {
    if (!user) return;
    checkBinding("douban").then((data) => {
      if (data.bound) {
        setDoubanBound(true);
        setDoubanProfile(data.profile ?? null);
        getCommunityData("douban").then((d) => {
          setBooks(d.books ?? []);
          setMovies(d.movies ?? []);
          setNotes(d.notes ?? []);
        });
      }
    });
  }, [user]);

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
        onScraping: (phase, counts) => {
          setScrapePhase(phase);
          setScrapeCounts(counts);
        },
        onBound: (_userId, profile, counts) => {
          setDoubanBound(true);
          setDoubanProfile(profile ?? null);
          setScrapeCounts(counts);
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
    setMenuOpen(false);
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

  const handleSync = async () => {
    setMenuOpen(false);
    setSyncing(true);
    setSyncPhase(undefined);
    try {
      await syncData("douban");
      wsRef.current = connectBindWs("douban", {
        onQr: () => {},
        onStatus: () => {},
        onScraping: (phase, counts) => {
          setSyncPhase(phase);
          setScrapeCounts(counts);
        },
        onBound: (_userId, _profile, counts) => {
          setScrapeCounts(counts);
          setSyncing(false);
        },
        onFailed: () => {
          setSyncing(false);
        },
      });
    } catch {
      setSyncing(false);
    }
  };

  const startEditProfile = () => {
    setEditName(user!.name);
    setEditBio(user!.bio ?? "");
    setEditAvatar(null);
    setProfileError(null);
    setEditingProfile(true);
  };

  const handleAvatarChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = async () => {
      const dataUrl = reader.result as string;
      setEditAvatar(dataUrl);
      try {
        await updateProfile({ avatar: dataUrl });
        await refreshUser();
        setEditAvatar(null);
      } catch {
        setProfileError("头像更新失败");
      }
    };
    reader.readAsDataURL(file);
  };

  const handleSaveProfile = async () => {
    setProfileSaving(true);
    setProfileError(null);
    try {
      await updateProfile({
        name: editName,
        bio: editBio || undefined,
        avatar: editAvatar !== null ? editAvatar : undefined,
      });
      await refreshUser();
      setEditingProfile(false);
    } catch {
      setProfileError("保存失败");
    }
    setProfileSaving(false);
  };

  const handleChangePw = async () => {
    setPwError(null);
    if (!newPw || newPw.length < 6) {
      setPwError("新密码至少需要 6 个字符");
      return;
    }
    setPwSaving(true);
    try {
      await changePassword(oldPw, newPw);
      setShowChangePw(false);
      setOldPw("");
      setNewPw("");
    } catch (e: any) {
      setPwError(e.message);
    }
    setPwSaving(false);
  };

  // Close menu on outside click
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    };
    if (menuOpen) document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [menuOpen]);

  // Cleanup WebSocket on unmount
  useEffect(() => () => closeWs(), [closeWs]);

  if (!user) {
    return <AuthModal onClose={onClose} />;
  }

  // Logged in: settings modal
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
                <h3 className="settings-title-row">
                  帐号管理
                  <span className="settings-title-actions">
                    {!editingProfile && (
                      <button className="icon-btn" onClick={startEditProfile} title="编辑资料">
                        <Pencil size={16} />
                      </button>
                    )}
                    {!showChangePw && !editingProfile && (
                      <button className="icon-btn" onClick={() => { setShowChangePw(true); setPwError(null); }} title="修改密码">
                        <KeyRound size={16} />
                      </button>
                    )}
                  </span>
                </h3>
                <div className="settings-profile">
                  <label className="profile-avatar-lg avatar-editable" title="更换头像">
                    <input type="file" accept="image/*" onChange={handleAvatarChange} style={{ display: "none" }} />
                    {editAvatar || user.avatar ? (
                      <img src={editAvatar || user.avatar!} alt="" className="profile-detail-avatar" />
                    ) : (
                      <User size={40} />
                    )}
                    <span className="avatar-edit-hint">更换</span>
                  </label>
                  {editingProfile ? (
                    <div className="profile-grid">
                      <div className="profile-field-edit">
                        <label>用户名</label>
                        <input
                          className="auth-input"
                          type="text"
                          value={editName}
                          onChange={(e) => setEditName(e.target.value)}
                        />
                      </div>
                      <div className="profile-field-edit">
                        <label>个人简介</label>
                        <input
                          className="auth-input"
                          type="text"
                          value={editBio}
                          onChange={(e) => setEditBio(e.target.value)}
                          placeholder="一句话介绍自己"
                        />
                      </div>
                      <div className="profile-field">
                        <label>邮箱</label>
                        <span>{user.email}</span>
                      </div>
                      <div className="profile-field">
                        <strong>{books.length}</strong>
                        <span>已读图书</span>
                      </div>
                      {profileError && <p className="auth-error">{profileError}</p>}
                      <div className="profile-edit-actions">
                        <button
                          className="auth-btn"
                          onClick={handleSaveProfile}
                          disabled={profileSaving}
                          style={{ flex: 1 }}
                        >
                          {profileSaving ? <Loader2 size={14} className="spin" /> : <><Check size={14} /> 保存</>}
                        </button>
                        <button
                          className="platform-bind-btn"
                          onClick={() => setEditingProfile(false)}
                          style={{ flex: 1 }}
                        >
                          取消
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="profile-grid">
                      <div className="profile-field">
                        <label>用户名</label>
                        <span>{user.name}</span>
                      </div>
                      <div className="profile-field">
                        <label>个人简介</label>
                        <span style={user.bio ? undefined : { color: "var(--text-muted)" }}>{user.bio || "一句话介绍自己"}</span>
                      </div>
                      <div className="profile-field">
                        <label>邮箱</label>
                        <span>{user.email}</span>
                      </div>
                      <div className="profile-field">
                        <strong>{books.length}</strong>
                        <span>已读图书</span>
                      </div>
                      <div className="profile-field">
                        <strong>{movies.length}</strong>
                        <span>已看电影</span>
                      </div>
                    </div>
                  )}
                </div>
                {showChangePw && (
                  <div style={{ marginTop: 12, display: "flex", flexDirection: "column", gap: 8, maxWidth: 320 }}>
                    <input
                      className="auth-input"
                      type="password"
                      placeholder="当前密码"
                      value={oldPw}
                      onChange={(e) => setOldPw(e.target.value)}
                    />
                    <input
                      className="auth-input"
                      type="password"
                      placeholder="新密码（至少 6 位）"
                      value={newPw}
                      onChange={(e) => setNewPw(e.target.value)}
                    />
                    {newPw && <StrengthBar level={getPasswordStrength(newPw)} />}
                    {pwError && <p className="auth-error">{pwError}</p>}
                    <div className="profile-edit-actions">
                      <button
                        className="auth-btn"
                        onClick={handleChangePw}
                        disabled={pwSaving}
                        style={{ flex: 1 }}
                      >
                        {pwSaving ? <Loader2 size={14} className="spin" /> : "确认修改"}
                      </button>
                      <button
                        className="platform-bind-btn"
                        onClick={() => { setShowChangePw(false); setOldPw(""); setNewPw(""); setPwError(null); }}
                        style={{ flex: 1 }}
                      >
                        取消
                      </button>
                    </div>
                  </div>
                )}
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
                                  {scrapeCounts.books != null && scrapeCounts.movies != null && (
                                    <> - 已导入 {scrapeCounts.books} 本图书, {scrapeCounts.movies} 部电影</>
                                  )}
                                </span>
                              )}
                            </div>
                          </div>
                          {doubanBound ? (
                            <div className="platform-actions">
                              <div className="dropdown-wrapper" ref={menuRef}>
                                <button
                                  className="platform-bind-btn"
                                  onClick={() => setMenuOpen((v) => !v)}
                                  disabled={refreshing || syncing}
                                >
                                  {refreshing || syncing ? (
                                    <>
                                      <Loader2 size={14} className="spin" />
                                      {refreshing && "更新中"}
                                      {syncing && syncPhase === "books" && "正在同步图书..."}
                                      {syncing && syncPhase === "movies" && "正在同步影视..."}
                                      {syncing && !syncPhase && "同步中..."}
                                    </>
                                  ) : (
                                    <>
                                      <RefreshCw size={14} />
                                      更新信息
                                      <ChevronDown size={12} />
                                    </>
                                  )}
                                </button>
                                {menuOpen && (
                                  <div className="dropdown-menu">
                                    <button className="dropdown-item" onClick={handleRefresh}>
                                      更新个人信息
                                    </button>
                                    <button className="dropdown-item" onClick={handleSync}>
                                      同步数据
                                    </button>
                                  </div>
                                )}
                              </div>
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
                                  {bindPhase === "scraping" && scrapePhase === "books" && "正在导入图书..."}
                                  {bindPhase === "scraping" && scrapePhase === "movies" && "正在导入影视..."}
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
                <div style={{ marginTop: 16 }}>
                  <button className="platform-bind-btn unbind" onClick={logout}>
                    退出登录
                  </button>
                </div>
              </div>
            )}
            {activeTab === "data" && (
              <div className="settings-page">
                <h3>数据管理</h3>
                {!doubanBound ? (
                  <p className="settings-desc">请先绑定账号以查看同步数据。</p>
                ) : (
                  <>
                    <div className="data-tabs">
                      <button
                        className={`data-tab ${dataTab === "books" ? "active" : ""}`}
                        onClick={() => setDataTab("books")}
                      >
                        图书 ({books.length})
                      </button>
                      <button
                        className={`data-tab ${dataTab === "movies" ? "active" : ""}`}
                        onClick={() => setDataTab("movies")}
                      >
                        电影 ({movies.length})
                      </button>
                      <button
                        className={`data-tab ${dataTab === "notes" ? "active" : ""}`}
                        onClick={() => setDataTab("notes")}
                      >
                        日记 ({notes.length})
                      </button>
                    </div>
                    <div className="data-list">
                      {dataTab === "books" && books.map((b) => (
                        <a key={b.url} href={b.url} target="_blank" rel="noreferrer" className="data-item">
                          {b.cover && <img src={b.cover} alt="" className="data-item-cover" />}
                          <div className="data-item-info">
                            <span className="data-item-title">{b.title}</span>
                            <span className="data-item-meta">
                              {b.author && `${b.author}`}
                              {b.author && b.publisher && " / "}
                              {b.publisher && `${b.publisher}`}
                              {b.rating && ` / ${"★".repeat(b.rating)}`}
                            </span>
                            {b.tags && b.tags.length > 0 && (
                              <div className="data-item-tags">
                                {b.tags.map((t) => <span key={t} className="data-tag">{t}</span>)}
                              </div>
                            )}
                          </div>
                        </a>
                      ))}
                      {dataTab === "movies" && movies.map((m) => (
                        <a key={m.url} href={m.url} target="_blank" rel="noreferrer" className="data-item">
                          {m.cover && <img src={m.cover} alt="" className="data-item-cover" />}
                          <div className="data-item-info">
                            <span className="data-item-title">{m.title}</span>
                            <span className="data-item-meta">
                              {m.release_date && `${m.release_date}`}
                              {m.rating && ` / ${"★".repeat(m.rating)}`}
                            </span>
                            {m.tags && m.tags.length > 0 && (
                              <div className="data-item-tags">
                                {m.tags.map((t) => <span key={t} className="data-tag">{t}</span>)}
                              </div>
                            )}
                          </div>
                        </a>
                      ))}
                      {dataTab === "notes" && notes.map((n, i) => (
                        n.url ? (
                          <a key={n.url} href={n.url} target="_blank" rel="noreferrer" className="data-item">
                            <div className="data-item-info">
                              <span className="data-item-title">{n.title}</span>
                              <span className="data-item-meta">
                                {n.date && n.date}
                                {n.location && ` / ${n.location}`}
                              </span>
                            </div>
                          </a>
                        ) : (
                          <div key={i} className="data-item">
                            <div className="data-item-info">
                              <span className="data-item-title">{n.title}</span>
                              <span className="data-item-meta">
                                {n.date && n.date}
                                {n.location && ` / ${n.location}`}
                              </span>
                            </div>
                          </div>
                        )
                      ))}
                      {dataTab === "books" && books.length === 0 && (
                        <p className="settings-desc">暂无图书数据，点击"同步数据"开始导入。</p>
                      )}
                      {dataTab === "movies" && movies.length === 0 && (
                        <p className="settings-desc">暂无影视数据，点击"同步数据"开始导入。</p>
                      )}
                      {dataTab === "notes" && notes.length === 0 && (
                        <p className="settings-desc">暂无日记数据，点击"同步数据"开始导入。</p>
                      )}
                    </div>
                  </>
                )}
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
