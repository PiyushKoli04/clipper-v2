import React from 'react';
import { Play, Flame } from 'lucide-react';
import { Clip } from '../types';

interface ClipCardProps {
  clip: Clip;
  onClick?: () => void;
  isActive?: boolean;
}

export const ClipCard: React.FC<ClipCardProps> = ({ clip, onClick, isActive = true }) => {
  const accentColor = clip.accent_color || '#6366F1';

  return (
    <div
      onClick={onClick}
      style={{
        borderColor: isActive ? `${accentColor}44` : 'rgba(255, 255, 255, 0.08)',
      }}
      className={`relative w-full aspect-[9/16] rounded-[32px] overflow-hidden cursor-pointer transition-all duration-300 shadow-glass border ${
        isActive ? 'scale-100 opacity-100' : 'scale-95 opacity-60'
      }`}
    >
      {/* Background Thumbnail Image or Gradient Fallback */}
      {clip.thumbnail_url ? (
        <img
          src={clip.thumbnail_url}
          alt={clip.hook_title}
          className="absolute inset-0 w-full h-full object-cover"
          loading="lazy"
        />
      ) : (
        <div
          className="absolute inset-0 w-full h-full flex items-center justify-center"
          style={{
            background: `radial-gradient(circle at center, ${accentColor}33 0%, #0B0D10 80%)`,
          }}
        >
          <div className="w-16 h-16 rounded-full glass-panel flex items-center justify-center text-white/40">
            <Play className="w-8 h-8 ml-1" />
          </div>
        </div>
      )}

      {/* Tint Glow from dominant accent color */}
      <div
        className="absolute -top-12 -left-12 w-48 h-48 rounded-full blur-3xl opacity-30 pointer-events-none"
        style={{ backgroundColor: accentColor }}
      />

      {/* Dark Bottom Gradient for Text Legibility */}
      <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/40 to-transparent pointer-events-none" />

      {/* Top Badges */}
      <div className="absolute top-4 left-4 right-4 flex items-center justify-between z-10 pointer-events-none">
        <span className="glass-pill px-3 py-1 text-[11px] font-bold text-white uppercase tracking-wider flex items-center gap-1 shadow-glass">
          <Flame className="w-3.5 h-3.5 text-amber-400 fill-amber-400" />
          {clip.virality_score}/100
        </span>

        <span className={`glass-pill px-3 py-1 text-[11px] font-semibold capitalize ${
          clip.status === 'approved' ? 'text-emerald-400 border-emerald-500/30' :
          clip.status === 'posted' ? 'text-blue-400 border-blue-500/30' :
          clip.status === 'rejected' ? 'text-red-400 border-red-500/30' : 'text-white/80'
        }`}>
          {clip.status}
        </span>
      </div>

      {/* Center Play Button Icon */}
      <div className="absolute inset-0 flex items-center justify-center z-10 pointer-events-none">
        <div className="w-14 h-14 rounded-full glass-panel-heavy flex items-center justify-center text-white border border-white/20 shadow-glow backdrop-blur-xl group-hover:scale-110 transition-transform">
          <Play className="w-6 h-6 ml-0.5 fill-white" />
        </div>
      </div>

      {/* Bottom Info */}
      <div className="absolute bottom-5 left-5 right-5 z-10 pointer-events-none">
        <h3 className="text-lg font-extrabold text-white line-clamp-2 leading-snug drop-shadow-md">
          {clip.hook_title}
        </h3>
        <p className="text-xs font-medium text-white/60 mt-1 flex items-center gap-1.5">
          <span>Reel</span>
          <span>•</span>
          <span>{Math.round(clip.duration)}s</span>
        </p>
      </div>
    </div>
  );
};

