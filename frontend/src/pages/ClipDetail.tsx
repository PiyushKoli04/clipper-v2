import React, { useState } from 'react';
import {
  ArrowLeft,
  MoreVertical,
  Play,
  Pause,
  Download,
  X,
  Check,
  Flame,
  Clock,
  Calendar,
  Send,
  Edit2,
} from 'lucide-react';
import { Clip } from '../types';
import { GlassButton } from '../components/GlassButton';

interface ClipDetailProps {
  clip: Clip;
  allClips: Clip[];
  onBack: () => void;
  onSelectClip: (clip: Clip) => void;
  onApproveAndPost: (clipId: string) => Promise<void>;
  onReject: (clipId: string) => Promise<void>;
  onUpdateCaption: (clipId: string, caption: string, hashtags: string) => Promise<void>;
}

export const ClipDetail: React.FC<ClipDetailProps> = ({
  clip,
  allClips,
  onBack,
  onSelectClip,
  onApproveAndPost,
  onReject,
  onUpdateCaption,
}) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [showMore, setShowMore] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [caption, setCaption] = useState(clip.ig_caption);
  const [hashtags, setHashtags] = useState(clip.hashtags);
  const [loadingAction, setLoadingAction] = useState(false);

  const accentColor = clip.accent_color || '#6366F1';
  const relatedClips = allClips.filter((c) => c.job_id === clip.job_id && c.id !== clip.id);

  const viralityTier =
    clip.virality_score >= 90 ? 'Viral 🔥' : clip.virality_score >= 75 ? 'Hot ⚡' : 'Solid 📈';

  const handleSaveCaption = async () => {
    setIsEditing(false);
    await onUpdateCaption(clip.id, caption, hashtags);
  };

  const handlePostAction = async () => {
    setLoadingAction(true);
    try {
      await onApproveAndPost(clip.id);
    } finally {
      setLoadingAction(false);
    }
  };

  const handleRejectAction = async () => {
    setLoadingAction(true);
    try {
      await onReject(clip.id);
    } finally {
      setLoadingAction(false);
    }
  };

  return (
    <div className="relative min-h-screen bg-darkBg text-white flex flex-col max-w-md mx-auto w-full overflow-x-hidden pb-12">
      {/* ── Full-Bleed Hero Video / Thumbnail ────────────────────── */}
      <div className="relative w-full aspect-[9/14] bg-black">
        {isPlaying && (clip.video_url || clip.preview_url) ? (
          <video
            src={clip.video_url || clip.preview_url}
            controls
            autoPlay
            playsInline
            className="w-full h-full object-cover"
            onEnded={() => setIsPlaying(false)}
          />
        ) : (
          <div
            className="relative w-full h-full cursor-pointer"
            onClick={() => setIsPlaying(true)}
          >
            {clip.thumbnail_url ? (
              <img
                src={clip.thumbnail_url}
                alt={clip.hook_title}
                className="w-full h-full object-cover"
              />
            ) : (
              <div
                className="w-full h-full flex items-center justify-center"
                style={{
                  background: `radial-gradient(circle at center, ${accentColor}44 0%, #0B0D10 90%)`,
                }}
              />
            )}
            {/* Center Play Button */}
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-16 h-16 rounded-full glass-panel-heavy flex items-center justify-center text-white border border-white/20 shadow-glow backdrop-blur-xl">
                <Play className="w-8 h-8 ml-1 fill-white" />
              </div>
            </div>
          </div>
        )}

        {/* Top Overlay Controls */}
        <div className="absolute top-4 left-4 right-4 flex items-center justify-between z-20 pointer-events-auto">
          <GlassButton
            variant="secondary"
            size="icon"
            onClick={onBack}
            aria-label="Back"
          >
            <ArrowLeft className="w-5 h-5" />
          </GlassButton>

          <GlassButton
            variant="secondary"
            size="icon"
            aria-label="More"
          >
            <MoreVertical className="w-5 h-5" />
          </GlassButton>
        </div>
      </div>

      {/* ── Tinted Draggable/Static Bottom Section ──────────────── */}
      <div
        style={{
          background: `linear-gradient(180deg, ${accentColor}25 0%, rgba(11, 13, 16, 0.98) 35%)`,
        }}
        className="relative -mt-8 rounded-t-[32px] px-5 pt-6 pb-8 border-t border-white/10 shadow-glass flex-1 flex flex-col"
      >
        {/* Title & Badge */}
        <div className="flex items-start justify-between gap-3 mb-2">
          <div>
            <h1 className="text-xl font-extrabold text-white leading-tight">
              {clip.hook_title}
            </h1>
            <p className="text-xs text-white/60 mt-1">Source Reel • 1080×1920</p>
          </div>

          <span
            style={{ backgroundColor: `${accentColor}33`, borderColor: `${accentColor}66` }}
            className="px-3 py-1 rounded-full text-xs font-bold text-white border whitespace-nowrap shadow-glass"
          >
            {viralityTier}
          </span>
        </div>

        {/* Stats Row */}
        <div className="grid grid-cols-3 gap-2 my-4">
          <div className="glass-panel p-3 rounded-28 flex flex-col items-center text-center">
            <Flame className="w-4 h-4 text-amber-400 mb-1" />
            <span className="text-[11px] text-white/50">Virality</span>
            <span className="text-sm font-bold text-white">{clip.virality_score}/100</span>
          </div>

          <div className="glass-panel p-3 rounded-28 flex flex-col items-center text-center">
            <Clock className="w-4 h-4 text-cyan-400 mb-1" />
            <span className="text-[11px] text-white/50">Duration</span>
            <span className="text-sm font-bold text-white">{Math.round(clip.duration)}s</span>
          </div>

          <div className="glass-panel p-3 rounded-28 flex flex-col items-center text-center">
            <Calendar className="w-4 h-4 text-purple-400 mb-1" />
            <span className="text-[11px] text-white/50">Status</span>
            <span className="text-xs font-bold text-white uppercase">{clip.status}</span>
          </div>
        </div>

        {/* AI Reason */}
        {clip.reason && (
          <div className="glass-panel p-3.5 rounded-28 mb-4">
            <span className="text-[10px] font-bold uppercase tracking-wider text-white/40 block mb-1">
              AI Selection Reason
            </span>
            <p className="text-xs text-white/80 leading-relaxed">{clip.reason}</p>
          </div>
        )}

        {/* Editable Instagram Caption & Hashtags */}
        <div className="glass-panel p-4 rounded-28 mb-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] font-bold uppercase tracking-wider text-white/40">
              Instagram Caption
            </span>
            <button
              onClick={() => (isEditing ? handleSaveCaption() : setIsEditing(true))}
              className="text-xs text-white/70 hover:text-white flex items-center gap-1 font-medium"
            >
              <Edit2 className="w-3 h-3" />
              <span>{isEditing ? 'Save' : 'Edit'}</span>
            </button>
          </div>

          {isEditing ? (
            <div className="space-y-2">
              <textarea
                value={caption}
                onChange={(e) => setCaption(e.target.value)}
                rows={3}
                className="w-full bg-white/5 rounded-xl p-2.5 text-xs text-white focus:outline-none focus:ring-1 focus:ring-white/30"
              />
              <input
                type="text"
                value={hashtags}
                onChange={(e) => setHashtags(e.target.value)}
                className="w-full bg-white/5 rounded-xl p-2 text-xs text-cyan-300 focus:outline-none"
              />
            </div>
          ) : (
            <div>
              <p className={`text-xs text-white/90 leading-relaxed ${showMore ? '' : 'line-clamp-2'}`}>
                {caption}
              </p>
              <p className="text-xs text-cyan-400/90 font-medium mt-2">{hashtags}</p>
              <button
                onClick={() => setShowMore(!showMore)}
                className="text-[11px] font-semibold text-white/50 hover:text-white/80 mt-1"
              >
                {showMore ? 'Show less' : 'Show more'}
              </button>
            </div>
          )}
        </div>

        {/* ── Main Actions Row ────────────────────────────────────── */}
        <div className="flex items-center gap-3 mb-6">
          {/* Big White Pill "Post Now" / "Approve" */}
          <GlassButton
            variant="primary"
            className="flex-1 text-sm py-3.5"
            disabled={loadingAction || clip.status === 'posted'}
            onClick={handlePostAction}
          >
            <Send className="w-4 h-4 mr-2" />
            {clip.status === 'approved'
              ? 'Post now to Reels'
              : clip.status === 'posted'
              ? 'Already Posted'
              : 'Approve & Post'}
          </GlassButton>

          {/* Circular Download Button */}
          <GlassButton
            variant="secondary"
            size="icon"
            onClick={() => {
              if (clip.video_url) window.open(clip.video_url, '_blank');
            }}
            aria-label="Download"
          >
            <Download className="w-4 h-4 text-white" />
          </GlassButton>

          {/* Circular Reject Button */}
          <GlassButton
            variant="danger"
            size="icon"
            disabled={loadingAction || clip.status === 'rejected'}
            onClick={handleRejectAction}
            aria-label="Reject"
          >
            <X className="w-4 h-4" />
          </GlassButton>
        </div>

        {/* ── More from this job ─────────────────────────────────── */}
        {relatedClips.length > 0 && (
          <div>
            <h4 className="text-xs font-bold text-white/60 uppercase tracking-wider mb-3">
              More from this video
            </h4>
            <div className="flex gap-3 overflow-x-auto no-scrollbar pb-2">
              {relatedClips.map((rel) => (
                <div
                  key={rel.id}
                  onClick={() => onSelectClip(rel)}
                  className="w-28 shrink-0 aspect-[9/16] rounded-2xl overflow-hidden glass-panel relative cursor-pointer active:scale-95 transition-transform"
                >
                  {rel.thumbnail_url ? (
                    <img
                      src={rel.thumbnail_url}
                      alt={rel.hook_title}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full bg-white/5 flex items-center justify-center">
                      <Play className="w-4 h-4 text-white/40" />
                    </div>
                  )}
                  <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent flex items-end p-2">
                    <p className="text-[10px] font-bold text-white line-clamp-2 leading-tight">
                      {rel.hook_title}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

