import { useState, useCallback } from "react";
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
  // Controls when the center-header expand button actually appears
  // Only becomes true after sidebar collapse animation finishes
  const [showExpandBtn, setShowExpandBtn] = useState(false);
  const [showProfile, setShowProfile] = useState(false);
  const store = useChatStore();
  const user: UserProfile | null = MOCK_USER;

  const handleWelcomeSend = (text: string) => {
    const id = store.createChat();
    store.updateTitle(id, text.slice(0, 30));
  };

  const handleCollapse = useCallback(() => {
    setSidebarOpen(false);
    // expand button will show after transitionend
  }, []);

  const handleExpand = useCallback(() => {
    setShowExpandBtn(false);
    setSidebarOpen(true);
  }, []);

  const handleTransitionEnd = useCallback(() => {
    if (!sidebarOpen) {
      setShowExpandBtn(true);
    }
  }, [sidebarOpen]);

  return (
    <div className="layout">
      <Sidebar
        open={sidebarOpen}
        chats={store.chats}
        activeChatId={store.activeChatId}
        user={user}
        onToggle={handleCollapse}
        onSelectChat={store.switchChat}
        onNewChat={() => store.switchChat(null)}
        onShowProfile={() => setShowProfile(true)}
        onTransitionEnd={handleTransitionEnd}
      />

      <main className="center">
        <div className="center-header">
          <button
            className={`sidebar-toggle ${showExpandBtn ? "visible" : ""}`}
            onClick={handleExpand}
          >
            <PanelRightOpen size={16} />
          </button>
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
