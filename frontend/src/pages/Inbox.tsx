import React, { useState } from 'react';
import {
  RotateCw,
  ExternalLink,
  CheckCircle2,
  XCircle,
  Clock,
  Sparkles,
  Bell,
  CheckCheck,
} from 'lucide-react';
import { Job, NotificationItem, JobStatus } from '../types';
import { GlassButton } from '../components/GlassButton';

interface InboxProps {
  jobs: Job[];
  notifications: NotificationItem[];
  loading: boolean;
  onRetryJob: (jobId: string) => Promise<void>;
  onRunJob: (jobId: string) => Promise<void>;
  onMarkNotificationRead: (notifId: string) => Promise<void>;
  onRefresh: () => Promise<void>;
}

const STAGES: { key: JobStatus; label: string }[] = [
  { key: 'queued', label: 'Queued' },
  { key: 'downloading', label: 'Download' },
  { key: 'transcribing', label: 'Transcribe' },
  { key: 'selecting', label: 'AI Highlights' },
  { key: 'rendering', label: 'Render 9:16' },
  { key: 'uploading', label: 'Upload' },
  { key: 'posting', label: 'Posting' },
  { key: 'done', label: 'Done' },
];

export const Inbox: React.FC<InboxProps> = ({
  jobs,
  notifications,
  loading,
  onRetryJob,
  onRunJob,
  onMarkNotificationRead,
  onRefresh,
}) => {
  const [activeTab, setActiveTab] = useState<'jobs' | 'notifications'>('jobs');
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const getStageProgress = (status: JobStatus) => {
    if (status === 'failed') return -1;
    const idx = STAGES.findIndex((s) => s.key === status);
    return idx >= 0 ? idx : 0;
  };

  const handleRetry = async (jobId: string) => {
    setActionLoading(jobId);
    try {
      await onRetryJob(jobId);
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <div className="flex flex-col min-h-screen pb-24 px-4 pt-3 max-w-md mx-auto w-full">
      {/* Header */}
      <header className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-extrabold tracking-tight text-white">Inbox & Activity</h1>
        <GlassButton
          variant="secondary"
          size="icon"
          onClick={onRefresh}
          aria-label="Refresh"
        >
          <RotateCw className="w-4 h-4 text-white/80" />
        </GlassButton>
      </header>

      {/* Tabs */}
      <div className="flex gap-2 glass-panel p-1 rounded-full mb-4">
        <button
          onClick={() => setActiveTab('jobs')}
          className={`flex-1 py-2 text-xs font-bold rounded-full transition-all ${
            activeTab === 'jobs' ? 'bg-white text-black shadow-glow' : 'text-white/60 hover:text-white'
          }`}
        >
          Pipelines ({jobs.length})
        </button>
        <button
          onClick={() => setActiveTab('notifications')}
          className={`flex-1 py-2 text-xs font-bold rounded-full transition-all flex items-center justify-center gap-1.5 ${
            activeTab === 'notifications'
              ? 'bg-white text-black shadow-glow'
              : 'text-white/60 hover:text-white'
          }`}
        >
          <span>Notifications</span>
          {notifications.filter((n) => !n.read).length > 0 && (
            <span className="w-2 h-2 rounded-full bg-red-500" />
          )}
        </button>
      </div>

      {/* ── Jobs Timeline Tab ────────────────────────────────────── */}
      {activeTab === 'jobs' && (
        <div className="space-y-4">
          {jobs.length === 0 ? (
            <div className="text-center py-12 glass-panel rounded-[32px] p-6">
              <Sparkles className="w-8 h-8 text-white/30 mx-auto mb-2" />
              <p className="text-sm font-semibold text-white/70">No clipping jobs yet</p>
              <p className="text-xs text-white/40 mt-1">Tap '+' below to process your first video URL.</p>
            </div>
          ) : (
            jobs.map((job) => {
              const currentStageIdx = getStageProgress(job.status);
              const isFailed = job.status === 'failed';
              const isDone = job.status === 'done';

              return (
                <div key={job.id} className="glass-panel p-4 rounded-28 border border-white/10 space-y-3">
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span
                          className={`w-2 h-2 rounded-full ${
                            isDone
                              ? 'bg-emerald-400 shadow-glow'
                              : isFailed
                              ? 'bg-red-500'
                              : 'bg-amber-400 animate-ping'
                          }`}
                        />
                        <span className="text-xs font-bold uppercase tracking-wider text-white">
                          {job.status}
                        </span>
                        {job.stage && (
                          <span className="text-[11px] text-white/40">({job.stage})</span>
                        )}
                      </div>
                      <p className="text-xs text-white/70 truncate font-mono">{job.source_url}</p>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-1.5 shrink-0">
                      {isFailed && (
                        <GlassButton
                          variant="secondary"
                          size="sm"
                          disabled={actionLoading === job.id}
                          onClick={() => handleRetry(job.id)}
                        >
                          <RotateCw className="w-3.5 h-3.5 mr-1" />
                          Retry
                        </GlassButton>
                      )}

                      {job.github_run_url && (
                        <a
                          href={job.github_run_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="p-2 rounded-full glass-panel hover:bg-white/10 text-white/60 hover:text-white"
                          title="View GitHub Actions Run"
                        >
                          <ExternalLink className="w-3.5 h-3.5" />
                        </a>
                      )}
                    </div>
                  </div>

                  {/* Stage Progress Indicator */}
                  {!isFailed && (
                    <div className="pt-1">
                      <div className="flex justify-between text-[10px] text-white/50 mb-1 font-medium">
                        <span>Queued</span>
                        <span>Transcribing</span>
                        <span>Rendering</span>
                        <span>Complete</span>
                      </div>
                      <div className="w-full h-1.5 bg-white/10 rounded-full overflow-hidden flex">
                        <div
                          style={{
                            width: `${Math.min(100, ((currentStageIdx + 1) / STAGES.length) * 100)}%`,
                          }}
                          className={`h-full transition-all duration-500 ${
                            isDone ? 'bg-emerald-400' : 'bg-gradient-to-r from-cyan-400 to-indigo-500'
                          }`}
                        />
                      </div>
                    </div>
                  )}

                  {/* Error display */}
                  {job.error && (
                    <div className="p-2.5 rounded-xl bg-red-500/10 border border-red-500/20 text-red-300 text-xs">
                      {job.error}
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      )}

      {/* ── Notifications Tab ────────────────────────────────────── */}
      {activeTab === 'notifications' && (
        <div className="space-y-3">
          {notifications.length === 0 ? (
            <div className="text-center py-12 glass-panel rounded-[32px] p-6">
              <Bell className="w-8 h-8 text-white/30 mx-auto mb-2" />
              <p className="text-sm font-semibold text-white/70">No notifications</p>
            </div>
          ) : (
            notifications.map((notif) => (
              <div
                key={notif.id}
                className={`glass-panel p-3.5 rounded-28 flex items-start gap-3 transition-opacity ${
                  notif.read ? 'opacity-60' : 'border-white/20'
                }`}
              >
                <div className="mt-0.5">
                  {notif.type === 'job_done' ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  ) : notif.type === 'job_failed' ? (
                    <XCircle className="w-4 h-4 text-red-400" />
                  ) : (
                    <Bell className="w-4 h-4 text-amber-400" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-white/90 leading-snug">{notif.message}</p>
                </div>
                {!notif.read && (
                  <button
                    onClick={() => onMarkNotificationRead(notif.id)}
                    className="p-1 rounded-full text-white/40 hover:text-white"
                    title="Mark as read"
                  >
                    <CheckCheck className="w-4 h-4" />
                  </button>
                )}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};

