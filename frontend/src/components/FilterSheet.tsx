import React, { useState } from 'react';
import { BottomSheet } from './BottomSheet';
import { GlassButton } from './GlassButton';

interface FilterSheetProps {
  isOpen: boolean;
  onClose: () => void;
  minScore: number;
  onApply: (minScore: number) => void;
  onReset: () => void;
}

export const FilterSheet: React.FC<FilterSheetProps> = ({
  isOpen,
  onClose,
  minScore: initialScore,
  onApply,
  onReset,
}) => {
  const [score, setScore] = useState(initialScore);

  return (
    <BottomSheet isOpen={isOpen} onClose={onClose} title="Filter Clips">
      <div className="space-y-6 pt-2">
        {/* Virality Score Slider */}
        <div className="glass-panel p-4 rounded-28">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-semibold text-white/90">Minimum Virality Score</span>
            <span className="px-2.5 py-1 rounded-full bg-white/10 text-xs font-bold text-white">
              {score}/100
            </span>
          </div>
          <input
            type="range"
            min="0"
            max="100"
            step="5"
            value={score}
            onChange={(e) => setScore(Number(e.target.value))}
            className="w-full accent-white h-2 bg-white/10 rounded-lg cursor-pointer"
          />
          <div className="flex justify-between text-[11px] text-white/40 mt-1">
            <span>All (0)</span>
            <span>Hot (75+)</span>
            <span>Viral (90+)</span>
          </div>
        </div>

        {/* Buttons */}
        <div className="flex gap-3 pt-2">
          <GlassButton
            variant="secondary"
            className="flex-1"
            onClick={() => {
              setScore(0);
              onReset();
              onClose();
            }}
          >
            Reset
          </GlassButton>
          <GlassButton
            variant="primary"
            className="flex-1"
            onClick={() => {
              onApply(score);
              onClose();
            }}
          >
            Apply Filters
          </GlassButton>
        </div>
      </div>
    </BottomSheet>
  );
};

