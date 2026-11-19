import React, { useState } from 'react';
import { Play, ListPlus, Sliders } from 'lucide-react';
import { BottomSheet } from '../components/BottomSheet';
import { GlassButton } from '../components/GlassButton';
import { JobOverrides } from '../types';

interface NewJobProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (url: string, overrides?: JobOverrides, runNow?: boolean) => Promise<void>;
}

export const NewJob: React.FC<NewJobProps> = ({ isOpen, onClose, onSubmit }) => {
  const [url, setUrl] = useState('');
  const [showOverrides, setShowOverrides] = useState(false);
  const [clipCount, setClipCount] = useState<number>(4);
  const [minSeconds, setMinSeconds] = useState<number>(20);
  const [maxSeconds, setMaxSeconds] = useState<number>(45);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (runNow: boolean) => {
    if (!url.trim()) {
      setError('Please provide a valid YouTube / video URL');
      return;
    }
    setError(null);
    setLoading(true);

    try {
      const overrides: JobOverrides = showOverrides
        ? { clip_count: clipCount, min_seconds: minSeconds, max_seconds: maxSeconds }
        : {};
      await onSubmit(url.trim(), overrides, runNow);
      setUrl('');
      setShowOverrides(false);
      onClose();
    } catch (err: any) {
      setError(err?.message || 'Failed to submit job');
    } finally {
      setLoading(false);
    }
  };

  return (
    <BottomSheet isOpen={isOpen} onClose={onClose} title="Create AI Clip Job">
      <div className="space-y-4 pt-1">
        <p className="text-xs text-white/60">
          Paste any YouTube URL or direct MP4 link. AI will analyze transcript, select the best viral hooks, crop to vertical 9:16, add karaoke captions, and render.
        </p>

        {/* Video URL Input */}
        <div className="glass-panel p-3 rounded-28">
          <label className="text-[10px] font-bold uppercase tracking-wider text-white/40 block mb-1">
            Video Source URL
          </label>
          <input
            type="url"
            placeholder="https://youtube.com/watch?v=..."
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            disabled={loading}
            className="w-full bg-transparent text-sm text-white placeholder-white/30 focus:outline-none"
          />
        </div>

        {error && (
          <div className="p-2.5 rounded-xl bg-red-500/20 border border-red-500/30 text-red-300 text-xs">
            {error}
          </div>
        )}

        {/* Optional Overrides Accordion */}
        <div className="glass-panel rounded-28 overflow-hidden">
          <button
            type="button"
            onClick={() => setShowOverrides(!showOverrides)}
            className="w-full p-3.5 flex items-center justify-between text-xs font-semibold text-white/80 hover:text-white"
          >
            <span className="flex items-center gap-2">
              <Sliders className="w-3.5 h-3.5 text-white/60" />
              Advanced Overrides (Optional)
            </span>
            <span className="text-[11px] text-white/40">{showOverrides ? 'Hide' : 'Configure'}</span>
          </button>

          {showOverrides && (
            <div className="px-4 pb-4 space-y-3 border-t border-white/5 pt-3">
              <div>
                <div className="flex justify-between text-xs text-white/70 mb-1">
                  <span>Target Clips:</span>
                  <span className="font-bold text-white">{clipCount}</span>
                </div>
                <input
                  type="range"
                  min="1"
                  max="8"
                  value={clipCount}
                  onChange={(e) => setClipCount(Number(e.target.value))}
                  className="w-full accent-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-[10px] text-white/50 block mb-1">Min Length (s)</label>
                  <input
                    type="number"
                    min="10"
                    max="60"
                    value={minSeconds}
                    onChange={(e) => setMinSeconds(Number(e.target.value))}
                    className="w-full bg-white/5 rounded-xl px-2.5 py-1.5 text-xs text-white focus:outline-none"
                  />
                </div>
                <div>
                  <label className="text-[10px] text-white/50 block mb-1">Max Length (s)</label>
                  <input
                    type="number"
                    min="20"
                    max="180"
                    value={maxSeconds}
                    onChange={(e) => setMaxSeconds(Number(e.target.value))}
                    className="w-full bg-white/5 rounded-xl px-2.5 py-1.5 text-xs text-white focus:outline-none"
                  />
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex gap-3 pt-2">
          <GlassButton
            variant="secondary"
            className="flex-1"
            disabled={loading}
            onClick={() => handleSubmit(false)}
          >
            <ListPlus className="w-4 h-4 mr-2" />
            Add to Queue
          </GlassButton>

          <GlassButton
            variant="primary"
            className="flex-1"
            disabled={loading}
            onClick={() => handleSubmit(true)}
          >
            <Play className="w-4 h-4 mr-2 fill-black" />
            Run Now
          </GlassButton>
        </div>
      </div>
    </BottomSheet>
  );
};

