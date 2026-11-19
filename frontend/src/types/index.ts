export interface ClipperConfig {
  storage_backend: 'r2' | 'gdrive';
  clips_per_video: number;
  min_clip_seconds: number;
  max_clip_seconds: number;
  caption_style: string;
  hashtags_default: string;
  dry_run: boolean;
  auto_post: boolean;
  max_posts_per_day: number;
  post_delay_min: number;
  post_delay_max: number;
  face_crop: boolean;
  cron_enabled: boolean;
  retention_days: number;
}

export interface JobOverrides {
  clip_count?: number;
  min_seconds?: number;
  max_seconds?: number;
}

export type JobStatus =
  | 'queued'
  | 'downloading'
  | 'transcribing'
  | 'selecting'
  | 'rendering'
  | 'uploading'
  | 'posting'
  | 'done'
  | 'failed';

export interface Job {
  id: string;
  source_url: string;
  status: JobStatus;
  stage: string;
  error?: string | null;
  overrides?: JobOverrides;
  created_at?: string | { _seconds: number; _nanoseconds: number };
  updated_at?: string | { _seconds: number; _nanoseconds: number };
  github_run_url?: string | null;
}

export type ClipStatus = 'rendered' | 'approved' | 'posted' | 'rejected';

export interface Clip {
  id: string;
  job_id: string;
  start: number;
  end: number;
  duration: number;
  hook_title: string;
  virality_score: number;
  reason: string;
  ig_caption: string;
  hashtags: string;
  storage_file_id?: string;
  video_url: string;
  preview_url: string;
  thumbnail_url: string;
  accent_color: string;
  status: ClipStatus;
  posted_at?: string;
  ig_media_pk?: string;
  created_at?: string;
}

export interface NotificationItem {
  id: string;
  type: 'job_done' | 'job_failed' | 'ig_challenge';
  message: string;
  read: boolean;
  created_at: string;
}

export interface InstagramHealth {
  health: 'ok' | 'challenge' | 'login_required' | 'cooldown';
  posts_today: number;
  last_post_at: string | null;
  has_session: boolean;
}

