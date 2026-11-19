import React from 'react';
import { Home, Film, Plus, Inbox, User } from 'lucide-react';

export type NavTab = 'home' | 'library' | 'new-job' | 'inbox' | 'profile';

interface BottomNavProps {
  currentTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  unreadCount?: number;
}

export const BottomNav: React.FC<BottomNavProps> = ({
  currentTab,
  onSelectTab,
  unreadCount = 0,
}) => {
  return (
    <div className="fixed bottom-0 left-0 right-0 z-40 flex justify-center pointer-events-none pb-[env(safe-area-inset-bottom,16px)]">
      <nav className="pointer-events-auto mx-4 mb-2 w-full max-w-md h-16 glass-panel-heavy rounded-full px-3 flex items-center justify-around shadow-glass border border-white/10">
        {/* Home */}
        <button
          onClick={() => onSelectTab('home')}
          className={`flex flex-col items-center justify-center min-w-[48px] min-h-[44px] relative transition-colors ${
            currentTab === 'home' ? 'text-white' : 'text-white/40 hover:text-white/70'
          }`}
          aria-label="Home"
        >
          <Home className="w-5 h-5" />
          <span className="text-[10px] mt-0.5 font-medium">Home</span>
          {currentTab === 'home' && (
            <span className="absolute bottom-1 w-1 h-1 rounded-full bg-white shadow-glow" />
          )}
        </button>

        {/* Library */}
        <button
          onClick={() => onSelectTab('library')}
          className={`flex flex-col items-center justify-center min-w-[48px] min-h-[44px] relative transition-colors ${
            currentTab === 'library' ? 'text-white' : 'text-white/40 hover:text-white/70'
          }`}
          aria-label="Library"
        >
          <Film className="w-5 h-5" />
          <span className="text-[10px] mt-0.5 font-medium">Library</span>
          {currentTab === 'library' && (
            <span className="absolute bottom-1 w-1 h-1 rounded-full bg-white shadow-glow" />
          )}
        </button>

        {/* Floating Raised Glowing "+" Button */}
        <div className="relative -top-5 flex items-center justify-center">
          <button
            onClick={() => onSelectTab('new-job')}
            className="w-13 h-13 p-3.5 rounded-full bg-white text-black shadow-glow hover:scale-105 active:scale-95 transition-all flex items-center justify-center min-h-[44px] min-w-[44px] border-4 border-darkBg"
            aria-label="New Job"
          >
            <Plus className="w-6 h-6 stroke-[2.5]" />
          </button>
        </div>

        {/* Inbox */}
        <button
          onClick={() => onSelectTab('inbox')}
          className={`flex flex-col items-center justify-center min-w-[48px] min-h-[44px] relative transition-colors ${
            currentTab === 'inbox' ? 'text-white' : 'text-white/40 hover:text-white/70'
          }`}
          aria-label="Inbox"
        >
          <div className="relative">
            <Inbox className="w-5 h-5" />
            {unreadCount > 0 && (
              <span className="absolute -top-1 -right-1 w-2 h-2 rounded-full bg-red-500 shadow-glow" />
            )}
          </div>
          <span className="text-[10px] mt-0.5 font-medium">Inbox</span>
          {currentTab === 'inbox' && (
            <span className="absolute bottom-1 w-1 h-1 rounded-full bg-white shadow-glow" />
          )}
        </button>

        {/* Profile */}
        <button
          onClick={() => onSelectTab('profile')}
          className={`flex flex-col items-center justify-center min-w-[48px] min-h-[44px] relative transition-colors ${
            currentTab === 'profile' ? 'text-white' : 'text-white/40 hover:text-white/70'
          }`}
          aria-label="Profile"
        >
          <User className="w-5 h-5" />
          <span className="text-[10px] mt-0.5 font-medium">Profile</span>
          {currentTab === 'profile' && (
            <span className="absolute bottom-1 w-1 h-1 rounded-full bg-white shadow-glow" />
          )}
        </button>
      </nav>
    </div>
  );
};

