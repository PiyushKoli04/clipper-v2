import React from 'react';

export const CardSkeleton: React.FC = () => {
  return (
    <div className="w-full aspect-[9/16] rounded-[32px] glass-panel animate-pulse p-4 flex flex-col justify-end overflow-hidden relative">
      <div className="absolute inset-0 bg-white/[0.03] animate-pulse" />
      <div className="w-3/4 h-5 bg-white/20 rounded-md mb-2" />
      <div className="w-1/2 h-3.5 bg-white/10 rounded-md mb-4" />
      <div className="w-full h-10 bg-white/10 rounded-full" />
    </div>
  );
};

export const TimelineSkeleton: React.FC = () => {
  return (
    <div className="space-y-4">
      {[1, 2, 3].map((i) => (
        <div key={i} className="glass-panel p-4 rounded-28 animate-pulse flex items-center gap-4">
          <div className="w-12 h-12 rounded-full bg-white/10" />
          <div className="flex-1 space-y-2">
            <div className="w-1/3 h-4 bg-white/20 rounded" />
            <div className="w-2/3 h-3 bg-white/10 rounded" />
          </div>
        </div>
      ))}
    </div>
  );
};

