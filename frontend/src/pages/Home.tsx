import React, { useState } from 'react';
import { Menu, Bell, Search, SlidersHorizontal } from 'lucide-react';
import { Clip } from '../types';
import { StatusChips, FilterStatus } from '../components/StatusChips';
import { Carousel } from '../components/Carousel';
import { CardSkeleton } from '../components/Skeleton';
import { FilterSheet } from '../components/FilterSheet';
import { GlassButton } from '../components/GlassButton';

interface HomeProps {
  clips: Clip[];
  loading: boolean;
  selectedStatus: FilterStatus;
  onSelectStatus: (status: FilterStatus) => void;
  searchQuery: string;
  onSearchChange: (q: string) => void;
  minScore: number;
  onApplyMinScore: (score: number) => void;
  onSelectClip: (clip: Clip) => void;
  unreadCount?: number;
  onOpenNotifications?: () => void;
}

export const Home: React.FC<HomeProps> = ({
  clips,
  loading,
  selectedStatus,
  onSelectStatus,
  searchQuery,
  onSearchChange,
  minScore,
  onApplyMinScore,
  onSelectClip,
  unreadCount = 0,
  onOpenNotifications,
}) => {
  const [filterOpen, setFilterOpen] = useState(false);

  return (
    <div className="flex flex-col min-h-screen pb-24 px-4 pt-3 max-w-md mx-auto w-full">
      {/* Header */}
      <header className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <GlassButton variant="secondary" size="icon" aria-label="Menu">
            <Menu className="w-5 h-5 text-white/80" />
          </GlassButton>
          <h1 className="text-xl font-extrabold tracking-tight text-white">Home</h1>
        </div>

        <GlassButton
          variant="secondary"
          size="icon"
          aria-label="Notifications"
          onClick={onOpenNotifications}
          className="relative"
        >
          <Bell className="w-5 h-5 text-white/80" />
          {unreadCount > 0 && (
            <span className="absolute top-2.5 right-2.5 w-2 h-2 rounded-full bg-red-500 shadow-glow" />
          )}
        </GlassButton>
      </header>

      {/* Search Bar + Filter Button */}
      <div className="flex items-center gap-2 mb-4">
        <div className="flex-1 flex items-center gap-2.5 px-4 py-2.5 glass-panel rounded-full focus-within:border-white/30 transition-all">
          <Search className="w-4 h-4 text-white/40 shrink-0" />
          <input
            type="text"
            placeholder="Search your clips"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-full bg-transparent text-sm text-white placeholder-white/40 focus:outline-none"
          />
        </div>

        <GlassButton
          variant={minScore > 0 ? 'primary' : 'secondary'}
          size="icon"
          onClick={() => setFilterOpen(true)}
          aria-label="Filter"
        >
          <SlidersHorizontal className="w-4 h-4" />
        </GlassButton>
      </div>

      {/* Status Chips */}
      <div className="mb-4">
        <StatusChips
          selected={selectedStatus}
          onSelect={onSelectStatus}
        />
      </div>

      {/* Center-Snapped Carousel */}
      <div className="flex-1 flex flex-col justify-center">
        {loading ? (
          <div className="w-[78%] mx-auto py-4">
            <CardSkeleton />
          </div>
        ) : (
          <Carousel clips={clips} onSelectClip={onSelectClip} />
        )}
      </div>

      {/* Filter Bottom Sheet */}
      <FilterSheet
        isOpen={filterOpen}
        onClose={() => setFilterOpen(false)}
        minScore={minScore}
        onApply={onApplyMinScore}
        onReset={() => onApplyMinScore(0)}
      />
    </div>
  );
};

