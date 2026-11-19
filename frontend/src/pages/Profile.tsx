import React, { useState } from 'react';
import {
  LogOut,
  Save,
  Instagram,
  Settings,
  HardDrive,
  Shield,
  Activity,
  CheckCircle2,
  AlertTriangle,
} from 'lucide-react';
import { ClipperConfig, InstagramHealth } from '../types';
import { GlassButton } from '../components/GlassButton';
import { useAuth } from '../contexts/AuthContext';

interface ProfileProps {
  config: ClipperConfig;
  igHealth?: InstagramHealth;
  onSaveConfig: (updated: ClipperConfig) => Promise<void>;
}

export const Profile: React.FC<ProfileProps> = ({
  config: initialConfig,
  igHealth,
  onSaveConfig,
}) => {
  const { user, signOut } = useAuth();
  const [form, setForm] = useState<ClipperConfig>(initialConfig);
  const [saving, setSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  const handleChange = (key: keyof ClipperConfig, value: any) => {
    setForm((prev) => ({ ...prev, [key]: value }));
    setSavedSuccess(false);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await onSaveConfig(form);
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 3000);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="flex flex-col min-h-screen pb-28 px-4 pt-3 max-w-md mx-auto w-full">
      {/* Header */}
      <header className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-extrabold tracking-tight text-white">Settings & Profile</h1>
        <GlassButton
          variant="secondary"
          size="sm"
          onClick={() => signOut()}
        >
          <LogOut className="w-3.5 h-3.5 mr-1.5" />
          Log out
        </GlassButton>
      </header>

      {/* User Info Card */}
      <div className="glass-panel p-4 rounded-28 mb-4 flex items-center gap-3">
        {user?.photoURL ? (
          <img src={user.photoURL} alt="" className="w-12 h-12 rounded-full border border-white/20" />
        ) : (
          <div className="w-12 h-12 rounded-full bg-indigo-600/30 border border-indigo-500/40 flex items-center justify-center font-bold text-lg text-white">
            {user?.email?.charAt(0).toUpperCase() || 'U'}
          </div>
        )}
        <div className="min-w-0 flex-1">
          <p className="text-sm font-bold text-white truncate">{user?.displayName || 'Clipper Creator'}</p>
          <p className="text-xs text-white/50 truncate">{user?.email || 'Authenticated User'}</p>
        </div>
      </div>

      {/* Instagram Session Health */}
      <div className="glass-panel p-4 rounded-28 mb-6 border border-white/10">
        <div className="flex items-center justify-between mb-3">
          <span className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-white/80">
            <Instagram className="w-4 h-4 text-pink-400" />
            Instagram Status
          </span>
          <span
            className={`text-[11px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1 ${
              igHealth?.health === 'ok'
                ? 'bg-emerald-500/20 text-emerald-400'
                : 'bg-amber-500/20 text-amber-300'
            }`}
          >
            {igHealth?.health === 'ok' ? (
              <CheckCircle2 className="w-3 h-3" />
            ) : (
              <AlertTriangle className="w-3 h-3" />
            )}
            {igHealth?.health || 'checking'}
          </span>
        </div>

        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="bg-white/5 p-2.5 rounded-xl">
            <span className="text-[10px] text-white/40 block">Posts Today</span>
            <span className="font-bold text-white text-sm">
              {igHealth?.posts_today || 0} / {form.max_posts_per_day}
            </span>
          </div>
          <div className="bg-white/5 p-2.5 rounded-xl">
            <span className="text-[10px] text-white/40 block">Session Health</span>
            <span className="font-bold text-white text-sm capitalize">
              {igHealth?.has_session ? 'Active' : 'No Session'}
            </span>
          </div>
        </div>
      </div>

      {/* ── Configuration Editor Form ────────────────────────────── */}
      <form onSubmit={handleSave} className="space-y-4">
        {/* Execution Mode Toggles */}
        <div className="glass-panel p-4 rounded-28 space-y-3">
          <span className="text-xs font-bold uppercase tracking-wider text-white/60 block">
            Automations & Safety
          </span>

          {/* Dry Run */}
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-bold text-white">Dry Run Mode</p>
              <p className="text-[11px] text-white/50">Skip Instagram upload/posting</p>
            </div>
            <input
              type="checkbox"
              checked={form.dry_run}
              onChange={(e) => handleChange('dry_run', e.target.checked)}
              className="w-5 h-5 accent-white rounded"
            />
          </div>

          {/* Auto Post */}
          <div className="flex items-center justify-between border-t border-white/5 pt-3">
            <div>
              <p className="text-xs font-bold text-white">Auto Post Approved</p>
              <p className="text-[11px] text-white/50">Post clips immediately after render</p>
            </div>
            <input
              type="checkbox"
              checked={form.auto_post}
              onChange={(e) => handleChange('auto_post', e.target.checked)}
              className="w-5 h-5 accent-white rounded"
            />
          </div>

          {/* Cron Enabled */}
          <div className="flex items-center justify-between border-t border-white/5 pt-3">
            <div>
              <p className="text-xs font-bold text-white">Cron Worker Enabled</p>
              <p className="text-[11px] text-white/50">Allow scheduled runs to pick queued jobs</p>
            </div>
            <input
              type="checkbox"
              checked={form.cron_enabled}
              onChange={(e) => handleChange('cron_enabled', e.target.checked)}
              className="w-5 h-5 accent-white rounded"
            />
          </div>
        </div>

        {/* Clip Generation Settings */}
        <div className="glass-panel p-4 rounded-28 space-y-3">
          <span className="text-xs font-bold uppercase tracking-wider text-white/60 block">
            Clip Parameters
          </span>

          <div className="flex justify-between items-center text-xs">
            <span className="text-white/80">Clips per video:</span>
            <input
              type="number"
              min="1"
              max="8"
              value={form.clips_per_video}
              onChange={(e) => handleChange('clips_per_video', Number(e.target.value))}
              className="w-16 bg-white/5 rounded-lg px-2 py-1 text-right text-white font-bold"
            />
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs pt-1">
            <div>
              <span className="text-white/50 block text-[10px] mb-1">Min Duration (s)</span>
              <input
                type="number"
                value={form.min_clip_seconds}
                onChange={(e) => handleChange('min_clip_seconds', Number(e.target.value))}
                className="w-full bg-white/5 rounded-lg p-2 text-white"
              />
            </div>
            <div>
              <span className="text-white/50 block text-[10px] mb-1">Max Duration (s)</span>
              <input
                type="number"
                value={form.max_clip_seconds}
                onChange={(e) => handleChange('max_clip_seconds', Number(e.target.value))}
                className="w-full bg-white/5 rounded-lg p-2 text-white"
              />
            </div>
          </div>

          <div className="pt-1">
            <span className="text-white/50 block text-[10px] mb-1">Default Hashtags</span>
            <input
              type="text"
              value={form.hashtags_default}
              onChange={(e) => handleChange('hashtags_default', e.target.value)}
              className="w-full bg-white/5 rounded-lg p-2 text-xs text-cyan-300"
            />
          </div>
        </div>

        {/* Storage & Limits */}
        <div className="glass-panel p-4 rounded-28 space-y-3">
          <span className="text-xs font-bold uppercase tracking-wider text-white/60 block">
            Storage & Limits
          </span>

          <div className="flex justify-between items-center text-xs">
            <span className="text-white/80">Storage Backend:</span>
            <select
              value={form.storage_backend}
              onChange={(e) => handleChange('storage_backend', e.target.value)}
              className="bg-darkBg border border-white/20 rounded-lg px-2.5 py-1 text-white text-xs font-semibold"
            >
              <option value="r2">Cloudflare R2 (Recommended)</option>
              <option value="gdrive">Google Drive (OAuth)</option>
            </select>
          </div>

          <div className="flex justify-between items-center text-xs">
            <span className="text-white/80">Retention days:</span>
            <input
              type="number"
              min="1"
              max="90"
              value={form.retention_days}
              onChange={(e) => handleChange('retention_days', Number(e.target.value))}
              className="w-16 bg-white/5 rounded-lg px-2 py-1 text-right text-white font-bold"
            />
          </div>

          <div className="flex justify-between items-center text-xs">
            <span className="text-white/80">Max posts per day:</span>
            <input
              type="number"
              min="1"
              max="25"
              value={form.max_posts_per_day}
              onChange={(e) => handleChange('max_posts_per_day', Number(e.target.value))}
              className="w-16 bg-white/5 rounded-lg px-2 py-1 text-right text-white font-bold"
            />
          </div>
        </div>

        {/* Save Button */}
        <div className="pt-2">
          <GlassButton
            type="submit"
            variant="primary"
            className="w-full py-3.5"
            disabled={saving}
          >
            <Save className="w-4 h-4 mr-2" />
            {saving ? 'Saving...' : savedSuccess ? 'Saved ✓' : 'Save Configuration'}
          </GlassButton>
        </div>
      </form>
    </div>
  );
};

