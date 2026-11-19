import React from 'react';
import { ShieldAlert } from 'lucide-react';

interface DryRunBannerProps {
  dryRun?: boolean;
}

export const DryRunBanner: React.FC<DryRunBannerProps> = ({ dryRun = true }) => {
  if (!dryRun) return null;

  return (
    <div className="w-full bg-amber-500/15 border-b border-amber-500/25 px-4 py-2 flex items-center justify-center gap-2 text-amber-300 text-xs font-semibold backdrop-blur-md sticky top-0 z-30">
      <ShieldAlert className="w-4 h-4 shrink-0 text-amber-400" />
      <span>Dry Run Active: Render clips locally, posting & upload skipped.</span>
    </div>
  );
};

