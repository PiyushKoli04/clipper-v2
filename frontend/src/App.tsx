import React, { useEffect, useState, useCallback } from 'react';
import { useAuth } from './contexts/AuthContext';
import { api } from './api/client';
import { Clip, Job, ClipperConfig, NotificationItem, InstagramHealth } from './types';
import { BottomNav, NavTab } from './components/BottomNav';
import { DryRunBanner } from './components/DryRunBanner';
import { FilterStatus } from './components/StatusChips';
import { Home } from './pages/Home';
import { Library } from './pages/Library';
import { NewJob } from './pages/NewJob';
import { Inbox } from './pages/Inbox';
import { Profile } from './pages/Profile';
import { ClipDetail } from './pages/ClipDetail';
import { GlassButton } from './components/GlassButton';
import { Sparkles, Film, LogIn } from 'lucide-react';

const DEFAULT_CONFIG: ClipperConfig = {
  storage_backend: 'r2',
  clips_per_video: 4,
  min_clip_seconds: 20,
  max_clip_seconds: 45,
  caption_style: 'bold_highlight',
  hashtags_default: '#reels #viral #clips',
  dry_run: true,
  auto_post: false,
  max_posts_per_day: 5,
  post_delay_min: 30,
  post_delay_max: 180,
  face_crop: false,
  cron_enabled: false,
  retention_days: 30,
};

export const App: React.FC = () => {
  const { user, loading: authLoading, signInWithGoogle, devSignIn, isDev } = useAuth();

  const [currentTab, setCurrentTab] = useState<NavTab>('home');
  const [selectedClip, setSelectedClip] = useState<Clip | null>(null);
  const [isNewJobOpen, setIsNewJobOpen] = useState(false);

  // Data states
  const [clips, setClips] = useState<Clip[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [config, setConfig] = useState<ClipperConfig>(DEFAULT_CONFIG);
  const [igHealth, setIgHealth] = useState<InstagramHealth | undefined>();

  // Filter states
  const [statusFilter, setStatusFilter] = useState<FilterStatus>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [minScore, setMinScore] = useState(0);

  const [loadingData, setLoadingData] = useState(true);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3500);
  };

  // Fetch all initial data
  const loadData = useCallback(async () => {
    if (!user) return;
    try {
      const [fetchedClips, fetchedJobs, fetchedConfig, fetchedNotifs, fetchedIg] =
        await Promise.allSettled([
          api.getClips(),
          api.getJobs(),
          api.getConfig(),
          api.getNotifications(),
          api.getInstagramHealth(),
        ]);

      if (fetchedClips.status === 'fulfilled') setClips(fetchedClips.value);
      if (fetchedJobs.status === 'fulfilled') setJobs(fetchedJobs.value);
      if (fetchedConfig.status === 'fulfilled') setConfig(fetchedConfig.value);
      if (fetchedNotifs.status === 'fulfilled') setNotifications(fetchedNotifs.value);
      if (fetchedIg.status === 'fulfilled') setIgHealth(fetchedIg.value);
    } catch (e) {
      console.error('Data load error:', e);
    } finally {
      setLoadingData(false);
    }
  }, [user]);

  useEffect(() => {
    if (user) {
      loadData();
      // Periodically refresh activity/notifications
      const interval = setInterval(() => {
        loadData();
      }, 15000);
      return () => clearInterval(interval);
    }
  }, [user, loadData]);

  // Auth gate
  if (authLoading) {
    return (
      <div className="min-h-screen bg-darkBg flex items-center justify-center p-4">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-2 border-white/20 border-t-white rounded-full animate-spin" />
          <p className="text-sm text-white/50 font-medium">Connecting to Clipper...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen bg-darkBg flex flex-col items-center justify-center p-6 text-center max-w-sm mx-auto">
        {/* Soft Background Glow */}
        <div className="absolute w-72 h-72 rounded-full bg-indigo-500/10 blur-[100px] pointer-events-none" />

        <div className="w-16 h-16 rounded-3xl glass-panel-heavy border border-white/20 flex items-center justify-center mb-6 shadow-glow">
          <Film className="w-8 h-8 text-white" />
        </div>

        <h1 className="text-2xl font-black text-white tracking-tight mb-2">
          Clipper <span className="text-indigo-400">v2</span>
        </h1>
        <p className="text-xs text-white/60 mb-8 leading-relaxed">
          Free, automated AI clipper agent. Turn long YouTube videos into viral captioned vertical shorts.
        </p>

        <div className="w-full space-y-3">
          <GlassButton
            variant="primary"
            className="w-full py-3.5"
            onClick={signInWithGoogle}
          >
            <LogIn className="w-4 h-4 mr-2" />
            Sign In with Google
          </GlassButton>

          {isDev && (
            <GlassButton
              variant="secondary"
              className="w-full py-3 text-xs"
              onClick={() => devSignIn()}
            >
              <Sparkles className="w-3.5 h-3.5 mr-2 text-indigo-400" />
              Dev Mode Bypass (Local Creator)
            </GlassButton>
          )}
        </div>
      </div>
    );
  }

  // Filtered Clips calculation
  const filteredClips = clips.filter((c) => {
    if (statusFilter !== 'all' && c.status !== statusFilter) return false;
    if (minScore > 0 && c.virality_score < minScore) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const match =
        c.hook_title.toLowerCase().includes(q) ||
        c.reason?.toLowerCase().includes(q) ||
        c.ig_caption?.toLowerCase().includes(q) ||
        c.hashtags?.toLowerCase().includes(q);
      if (!match) return false;
    }
    return true;
  });

  const unreadNotifsCount = notifications.filter((n) => !n.read).length;

  // Handlers
  const handleCreateJob = async (url: string, overrides?: any, runNow = false) => {
    const res = await api.createJob(url, overrides, runNow);
    showToast(runNow ? 'Job created and dispatched!' : 'Job added to queue!');
    loadData();
    setCurrentTab('inbox');
  };

  const handleApproveAndPost = async (clipId: string) => {
    // Optimistic UI update
    setClips((prev) =>
      prev.map((c) => (c.id === clipId ? { ...c, status: 'approved' } : c))
    );
    if (selectedClip && selectedClip.id === clipId) {
      setSelectedClip({ ...selectedClip, status: 'approved' });
    }
    await api.postClip(clipId);
    showToast('Clip approved and post workflow queued!');
    loadData();
  };

  const handleRejectClip = async (clipId: string) => {
    setClips((prev) =>
      prev.map((c) => (c.id === clipId ? { ...c, status: 'rejected' } : c))
    );
    if (selectedClip && selectedClip.id === clipId) {
      setSelectedClip({ ...selectedClip, status: 'rejected' });
    }
    await api.updateClip(clipId, { status: 'rejected' });
    showToast('Clip marked as rejected');
    loadData();
  };

  const handleUpdateCaption = async (clipId: string, caption: string, hashtags: string) => {
    setClips((prev) =>
      prev.map((c) => (c.id === clipId ? { ...c, ig_caption: caption, hashtags } : c))
    );
    if (selectedClip && selectedClip.id === clipId) {
      setSelectedClip({ ...selectedClip, ig_caption: caption, hashtags });
    }
    await api.updateClip(clipId, { ig_caption: caption, hashtags });
    showToast('Caption saved');
  };

  return (
    <div className="relative min-h-screen bg-darkBg text-primaryText flex flex-col items-center">
      {/* Background Soft Glows */}
      <div className="fixed top-0 left-1/2 -translate-x-1/2 w-96 h-96 rounded-full bg-indigo-600/10 blur-[120px] pointer-events-none" />
      <div className="fixed bottom-20 left-1/2 -translate-x-1/2 w-80 h-80 rounded-full bg-cyan-600/10 blur-[120px] pointer-events-none" />

      {/* Dry Run Banner */}
      <DryRunBanner dryRun={config.dry_run} />

      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed top-4 z-50 px-4 py-2.5 rounded-full bg-white text-black font-semibold text-xs shadow-glow animate-fade-in flex items-center gap-2">
          <Sparkles className="w-3.5 h-3.5" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Main Screen Content */}
      <div className="w-full max-w-md flex-1 flex flex-col">
        {selectedClip ? (
          <ClipDetail
            clip={selectedClip}
            allClips={clips}
            onBack={() => setSelectedClip(null)}
            onSelectClip={(c) => setSelectedClip(c)}
            onApproveAndPost={handleApproveAndPost}
            onReject={handleRejectClip}
            onUpdateCaption={handleUpdateCaption}
          />
        ) : (
          <>
            {currentTab === 'home' && (
              <Home
                clips={filteredClips}
                loading={loadingData}
                selectedStatus={statusFilter}
                onSelectStatus={setStatusFilter}
                searchQuery={searchQuery}
                onSearchChange={setSearchQuery}
                minScore={minScore}
                onApplyMinScore={setMinScore}
                onSelectClip={(c) => setSelectedClip(c)}
                unreadCount={unreadNotifsCount}
                onOpenNotifications={() => setCurrentTab('inbox')}
              />
            )}

            {currentTab === 'library' && (
              <Library
                clips={filteredClips}
                loading={loadingData}
                selectedStatus={statusFilter}
                onSelectStatus={setStatusFilter}
                searchQuery={searchQuery}
                onSearchChange={setSearchQuery}
                onSelectClip={(c) => setSelectedClip(c)}
              />
            )}

            {currentTab === 'inbox' && (
              <Inbox
                jobs={jobs}
                notifications={notifications}
                loading={loadingData}
                onRetryJob={async (id) => {
                  await api.retryJob(id);
                  showToast('Job retry dispatched!');
                  loadData();
                }}
                onRunJob={async (id) => {
                  await api.runJob(id);
                  showToast('Job run dispatched!');
                  loadData();
                }}
                onMarkNotificationRead={async (nid) => {
                  await api.markNotificationRead(nid);
                  setNotifications((prev) =>
                    prev.map((n) => (n.id === nid ? { ...n, read: true } : n))
                  );
                }}
                onRefresh={async () => {
                  await loadData();
                  showToast('Refreshed');
                }}
              />
            )}

            {currentTab === 'profile' && (
              <Profile
                config={config}
                igHealth={igHealth}
                onSaveConfig={async (updated) => {
                  const saved = await api.updateConfig(updated);
                  setConfig(saved);
                  showToast('Configuration updated');
                }}
              />
            )}

            {/* Bottom Nav Bar (hidden when viewing clip detail) */}
            <BottomNav
              currentTab={currentTab}
              onSelectTab={(tab) => {
                if (tab === 'new-job') {
                  setIsNewJobOpen(true);
                } else {
                  setCurrentTab(tab);
                }
              }}
              unreadCount={unreadNotifsCount}
            />
          </>
        )}
      </div>

      {/* New Job Bottom Sheet */}
      <NewJob
        isOpen={isNewJobOpen}
        onClose={() => setIsNewJobOpen(false)}
        onSubmit={handleCreateJob}
      />
    </div>
  );
};

