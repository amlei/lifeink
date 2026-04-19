import { useState, useEffect, useCallback } from "react";
import {
  PanelRightOpen,
  PanelRightClose,
  Plus,
  Send,
  User,
  Settings,
  LogIn,
  X,
} from "lucide-react";
import "./App.css";

interface Message {
  role: "user" | "ai";
  content: string;
}

interface Chat {
  id: string;
  title: string;
  messages: Message[];
}

const MOCK_CHATS: Chat[] = [
  {
    id: "1",
    title: "Read something about...",
    messages: [
      { role: "user", content: "Based on my reading history, recommend me some history books." },
      {
        role: "ai",
        content:
          "Based on your Douban reading records, you rated *Jian Shang* 5 stars and tagged it \"history.\" Here are some recommendations:\n\n1. **The Guns of August** - Barbara Tuchman\n2. **SPQR** - Mary Beard\n3. **The Silk Roads** - Peter Frankopan\n\nYou seem to enjoy narratives that blend archaeology with historical analysis. These should be a great fit.",
      },
    ],
  },
  {
    id: "2",
    title: "My reading stats this year",
    messages: [
      { role: "user", content: "Show me my reading stats for this year." },
      {
        role: "ai",
        content:
          "Here are your 2026 reading stats so far:\n\n- **Books read:** 12\n- **Average rating:** 4.2 / 5\n- **Most-read genre:** History (5 books)\n- **Highest rated:** *Jian Shang* (5 stars)\n\nYou're on track to surpass last year's total of 28 books!",
      },
    ],
  },
  {
    id: "3",
    title: "Movie recommendations based on...",
    messages: [
      { role: "user", content: "Recommend movies similar to my favorites." },
      {
        role: "ai",
        content:
          "Your top-rated movies include *Interstellar* and *Blade Runner 2049*. Based on your taste for sci-fi with emotional depth:\n\n1. **Arrival** (2016)\n2. **Ex Machina** (2014)\n3. **Dune: Part Two** (2024)\n\nWant me to generate a detailed comparison report?",
      },
    ],
  },
];

interface UserProfile {
  name: string;
  avatar: string;
  email: string;
  doubanId: string;
  booksRead: number;
  moviesWatched: number;
}

const MOCK_USER: UserProfile | null = {
  name: "Amlei",
  avatar: "",
  email: "user@example.com",
  doubanId: "amlei",
  booksRead: 42,
  moviesWatched: 128,
};

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [chats] = useState<Chat[]>(MOCK_CHATS);
  const [activeChat, setActiveChat] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [user] = useState<UserProfile | null>(MOCK_USER);
  const [showProfile, setShowProfile] = useState(false);
  const [loading, setLoading] = useState(false);

  const switchChat = useCallback(
    (id: string | null) => {
      if (id === activeChat) return;
      setLoading(true);
      setTimeout(() => {
        setActiveChat(id);
        setInput("");
        setLoading(false);
      }, 300);
    },
    [activeChat],
  );

  const handleNewChat = useCallback(() => {
    switchChat(null);
  }, [switchChat]);

  useEffect(() => {
    setLoading(false);
  }, []);

  const currentChat = chats.find((c) => c.id === activeChat);

  return (
    <div className="layout">
      {/* Left Sidebar */}
      <aside className={`sidebar ${sidebarOpen ? "" : "collapsed"}`}>
        <div className="sidebar-header">
          <span className="sidebar-title">History</span>
          <button
            className="sidebar-toggle"
            onClick={() => setSidebarOpen(false)}
          >
            <PanelRightClose size={16} />
          </button>
        </div>

        <button className="new-chat-btn" onClick={handleNewChat}>
          <Plus size={15} />
          New Chat
        </button>

        <div className="sidebar-list">
          {chats.map((chat) => (
            <div
              key={chat.id}
              className={`chat-item ${activeChat === chat.id ? "active" : ""}`}
              onClick={() => switchChat(chat.id)}
            >
              {chat.title}
            </div>
          ))}
        </div>

        <div className="sidebar-footer">
          {user ? (
            <div className="user-info" onClick={() => setShowProfile(true)}>
              <div className="user-avatar">
                <User size={16} />
              </div>
              <span className="user-name">{user.name}</span>
              <Settings size={14} className="user-settings-icon" />
            </div>
          ) : (
            <div className="user-info user-login" onClick={() => setShowProfile(true)}>
              <LogIn size={16} />
              <span>Login</span>
            </div>
          )}
        </div>
      </aside>

      {/* Center */}
      <main className="center">
        <div className="center-header">
          <button
            className={`sidebar-toggle ${!sidebarOpen ? "visible" : ""}`}
            onClick={() => setSidebarOpen(true)}
          >
            <PanelRightOpen size={16} />
          </button>
          <span className="center-header-title">
            {activeChat
              ? chats.find((c) => c.id === activeChat)?.title
              : "LifeInk AI"}
          </span>
        </div>

        <div className="chat-area">
          {loading ? (
            <div className="loading-overlay">
              <div className="loading-spinner" />
            </div>
          ) : !activeChat ? (
            <div className="welcome fade-in">
              <div className="brand">LifeInk AI</div>
              <div className="input-box">
                <textarea
                  rows={2}
                  placeholder="Ask about your reading, movies, journals..."
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                />
                <button className="send-btn">
                  <Send size={16} />
                </button>
              </div>
            </div>
          ) : (
            <>
              <div className="messages">
                {currentChat?.messages.map((msg, i) => (
                  <div key={i} className={`message message-${msg.role}`}>
                    <div className="message-content">
                      {msg.content.split("\n").map((line, j) => (
                        <p key={j}>{line}</p>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
              <div className="chat-input-bar">
                <div className="input-box">
                  <textarea
                    rows={2}
                    placeholder="Continue the conversation..."
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                  />
                  <button className="send-btn">
                    <Send size={16} />
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </main>

      {/* Right Panel (placeholder) */}
      <aside className="right-panel" />

      {/* Profile Modal */}
      {showProfile && user && (
        <div className="modal-overlay" onClick={() => setShowProfile(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Profile</h2>
              <button className="modal-close" onClick={() => setShowProfile(false)}>
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
      )}
    </div>
  );
}

export default App;
