import React from 'react';
import { ClipStatus } from '../types';

export type FilterStatus = 'all' | ClipStatus;

interface StatusChipsProps {
  selected: FilterStatus;
  onSelect: (status: FilterStatus) => void;
  counts?: Partial<Record<FilterStatus, number>>;
}

const CHIPS: { id: FilterStatus; label: string }[] = [
  { id: 'all', label: 'All' },
  { id: 'rendered', label: 'Rendered' },
  { id: 'approved', label: 'Approved' },
  { id: 'posted', label: 'Posted' },
  { id: 'rejected', label: 'Rejected' },
];

export const StatusChips: React.FC<StatusChipsProps> = ({
  selected,
  onSelect,
  counts,
}) => {
  return (
    <div className="flex items-center gap-2 overflow-x-auto no-scrollbar py-1 px-4 -mx-4">
      {CHIPS.map((chip) => {
        const isActive = selected === chip.id;
        const count = counts ? counts[chip.id] : undefined;

        return (
          <button
            key={chip.id}
            onClick={() => onSelect(chip.id)}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-full text-xs font-semibold whitespace-nowrap transition-all min-h-[36px] active:scale-95 ${
              isActive
                ? 'bg-white text-black shadow-glow font-bold'
                : 'glass-panel text-white/70 hover:text-white hover:bg-white/10'
            }`}
          >
            <span>{chip.label}</span>
            {count !== undefined && (
              <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${
                isActive ? 'bg-black/15 text-black' : 'bg-white/10 text-white/60'
              }`}>
                {count}
              </span>
            )}
            {/* Active tab dot */}
            {isActive && (
              <span className="w-1.5 h-1.5 rounded-full bg-black ml-0.5" />
            )}
          </button>
        );
      })}
    </div>
  );
};

