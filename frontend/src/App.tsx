import { useState } from "react";
import { PanelRightOpen } from "lucide-react";
import type { UserProfile } from "./types";
import { useChatStore } from "./hooks/useChatStore";
import { Sidebar } from "./components/Sidebar";
import { WelcomeScreen } from "./components/WelcomeScreen";
import { ChatPanel } from "./components/ChatPanel";
import { ProfileModal } from "./components/ProfileModal";
import "./App.css";

const MOCK_USER: UserProfile = {
  name: "Amlei",
  avatar: "",
  email: "user@example.com",
  doubanId: "amlei",
  booksRead: 42,
  moviesWatched: 128,
};

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [showProfile, setShowProfile] = useState(false);
  const store = useChatStore();
  const user: UserProfile | null = MOCK_USER;

  const handleWelcomeSend = (text: string) => {
    const id = store.createChat();
    store.updateTitle(id, text.slice(0, 30));
  };

  return (
    <div className="layout">
      <Sidebar
        open={sidebarOpen}
        chats={store.chats}
        activeChatId={store.activeChatId}
        user={user}
        onToggle={() => setSidebarOpen(false)}
        onSelectChat={store.switchChat}
        onNewChat={() => store.switchChat(null)}
        onShowProfile={() => setShowProfile(true)}
      />

      <main className="center">
        <div className="center-header">
          <button
            className={`sidebar-toggle ${!sidebarOpen ? "visible" : ""}`}
            onClick={() => setSidebarOpen(true)}
          >
            <PanelRightOpen size={16} />
          </button>
          <span className="center-header-title">
            {store.activeChatId
              ? store.chats.find((c) => c.id === store.activeChatId)?.title ??
                "LifeInk AI"
              : "LifeInk AI"}
          </span>
        </div>

        <div className="chat-area">
          {store.activeChatId ? (
            <ChatPanel chatId={store.activeChatId} store={store} />
          ) : (
            <WelcomeScreen onSend={handleWelcomeSend} />
          )}
        </div>
      </main>

      <aside className="right-panel" />

      {showProfile && user && (
        <ProfileModal user={user} onClose={() => setShowProfile(false)} />
      )}
    </div>
  );
}

export default App;
