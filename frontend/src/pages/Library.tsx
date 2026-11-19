import React, { useState } from 'react';
import { Search, LayoutGrid, List } from 'lucide-react';
import { Clip } from '../types';
import { StatusChips, FilterStatus } from '../components/StatusChips';
import { ClipCard } from '../components/ClipCard';
import { CardSkeleton } from '../components/Skeleton';
import { GlassButton } from '../components/GlassButton';

interface LibraryProps {
  clips: Clip[];
  loading: boolean;
  selectedStatus: FilterStatus;
  onSelectStatus: (status: FilterStatus) => void;
  searchQuery: string;
  onSearchChange: (q: string) => void;
  onSelectClip: (clip: Clip) => void;
}

export const Library: React.FC<LibraryProps> = ({
  clips,
  loading,
  selectedStatus,
  onSelectStatus,
  searchQuery,
  onSearchChange,
  onSelectClip,
}) => {
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

  return (
    <div className="flex flex-col min-h-screen pb-24 px-4 pt-3 max-w-md mx-auto w-full">
      {/* Header */}
      <header className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-extrabold tracking-tight text-white">Library</h1>
        <div className="flex items-center gap-1.5 glass-panel rounded-full p-1">
          <button
            onClick={() => setViewMode('grid')}
            className={`p-1.5 rounded-full transition-colors ${
              viewMode === 'grid' ? 'bg-white text-black' : 'text-white/60 hover:text-white'
            }`}
            aria-label="Grid view"
          >
            <LayoutGrid className="w-4 h-4" />
          </button>
          <button
            onClick={() => setViewMode('list')}
            className={`p-1.5 rounded-full transition-colors ${
              viewMode === 'list' ? 'bg-white text-black' : 'text-white/60 hover:text-white'
            }`}
            aria-label="List view"
          >
            <List className="w-4 h-4" />
          </button>
        </div>
      </header>

      {/* Search Input */}
      <div className="flex items-center gap-2.5 px-4 py-2.5 glass-panel rounded-full focus-within:border-white/30 transition-all mb-4">
        <Search className="w-4 h-4 text-white/40 shrink-0" />
        <input
          type="text"
          placeholder="Filter clips by title, caption..."
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          className="w-full bg-transparent text-sm text-white placeholder-white/40 focus:outline-none"
        />
      </div>

      {/* Status Chips */}
      <div className="mb-4">
        <StatusChips selected={selectedStatus} onSelect={onSelectStatus} />
      </div>

      {/* Clip Content */}
      {loading ? (
        <div className="grid grid-cols-2 gap-3">
          <CardSkeleton />
          <CardSkeleton />
        </div>
      ) : clips.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center text-center p-8 glass-panel rounded-[32px] my-8">
          <p className="text-white/60 font-semibold">No clips found</p>
          <p className="text-xs text-white/40 mt-1">Try changing your search or status filter.</p>
        </div>
      ) : viewMode === 'grid' ? (
        <div className="grid grid-cols-2 gap-3">
          {clips.map((clip) => (
            <div key={clip.id} className="cursor-pointer" onClick={() => onSelectClip(clip)}>
              <ClipCard clip={clip} />
            </div>
          ))}
        </div>
      ) : (
        <div className="space-y-3">
          {clips.map((clip) => (
            <div
              key={clip.id}
              onClick={() => onSelectClip(clip)}
              className="glass-panel p-3 rounded-28 flex items-center gap-3 cursor-pointer hover:bg-white/10 active:scale-[0.99] transition-all"
            >
              <div className="w-16 h-24 rounded-2xl overflow-hidden bg-black shrink-0 relative">
                {clip.thumbnail_url ? (
                  <img src={clip.thumbnail_url} alt="" className="w-full h-full object-cover" />
                ) : (
                  <div className="w-full h-full bg-white/10" />
                )}
                <span className="absolute bottom-1 right-1 text-[9px] font-bold px-1 rounded bg-black/60 text-white">
                  {Math.round(clip.duration)}s
                </span>
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300">
                    {clip.virality_score}/100
                  </span>
                  <span className="text-[10px] uppercase font-semibold text-white/50">
                    {clip.status}
                  </span>
                </div>
                <h4 className="text-xs font-bold text-white line-clamp-2 leading-snug">
                  {clip.hook_title}
                </h4>
                <p className="text-[11px] text-white/50 mt-1 truncate">{clip.ig_caption}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

