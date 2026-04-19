import { useState } from "react";
import {
  PanelRightOpen,
  PanelRightClose,
  Plus,
  Send,
} from "lucide-react";
import "./App.css";

interface Chat {
  id: string;
  title: string;
}

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [chats] = useState<Chat[]>([
    { id: "1", title: "Read something about..." },
    { id: "2", title: "My reading stats this year" },
    { id: "3", title: "Movie recommendations based on..." },
  ]);
  const [activeChat, setActiveChat] = useState<string | null>(null);
  const [input, setInput] = useState("");

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

        <button className="new-chat-btn">
          <Plus size={15} />
          New Chat
        </button>

        <div className="sidebar-list">
          {chats.map((chat) => (
            <div
              key={chat.id}
              className={`chat-item ${activeChat === chat.id ? "active" : ""}`}
              onClick={() => setActiveChat(chat.id)}
            >
              {chat.title}
            </div>
          ))}
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
          {!activeChat && (
            <div className="welcome">
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
          )}
        </div>
      </main>

      {/* Right Panel (placeholder) */}
      <aside className="right-panel" />
    </div>
  );
}

export default App;
