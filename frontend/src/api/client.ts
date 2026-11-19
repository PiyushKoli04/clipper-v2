import { ClipperConfig, Clip, Job, NotificationItem, InstagramHealth, JobOverrides } from '../types';

let currentAuthToken: string | null = null;

export const setAuthToken = (token: string | null) => {
  currentAuthToken = token;
};

const getHeaders = () => {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (currentAuthToken) {
    headers['Authorization'] = `Bearer ${currentAuthToken}`;
  } else {
    // In dev mode when not signed in, pass mock token for convenience
    headers['Authorization'] = 'Bearer mock-token';
  }
  return headers;
};

export const api = {
  // Public config for Firebase initialization
  getPublicConfig: async (): Promise<{ firebase: Record<string, string> }> => {
    try {
      const res = await fetch('/api/public-config');
      if (res.ok) return await res.json();
    } catch (e) {
      console.warn('Failed to fetch public config', e);
    }
    return { firebase: {} };
  },

  // Config
  getConfig: async (): Promise<ClipperConfig> => {
    const res = await fetch('/api/config', { headers: getHeaders() });
    if (!res.ok) throw new Error('Failed to load configuration');
    return res.json();
  },

  updateConfig: async (config: ClipperConfig): Promise<ClipperConfig> => {
    const res = await fetch('/api/config', {
      method: 'PUT',
      headers: getHeaders(),
      body: JSON.stringify(config),
    });
    if (!res.ok) throw new Error('Failed to update configuration');
    return res.json();
  },

  // Jobs
  getJobs: async (limit = 50): Promise<Job[]> => {
    const res = await fetch(`/api/jobs?limit=${limit}`, { headers: getHeaders() });
    if (!res.ok) throw new Error('Failed to load jobs');
    return res.json();
  },

  createJob: async (source_url: string, overrides?: JobOverrides, run_now = false) => {
    const res = await fetch('/api/jobs', {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ source_url, overrides, run_now }),
    });
    if (!res.ok) throw new Error('Failed to create job');
    return res.json();
  },

  runJob: async (jobId: string) => {
    const res = await fetch(`/api/jobs/${jobId}/run`, {
      method: 'POST',
      headers: getHeaders(),
    });
    if (!res.ok) throw new Error('Failed to trigger job');
    return res.json();
  },

  retryJob: async (jobId: string) => {
    const res = await fetch(`/api/jobs/${jobId}/retry`, {
      method: 'POST',
      headers: getHeaders(),
    });
    if (!res.ok) throw new Error('Failed to retry job');
    return res.json();
  },

  // Clips
  getClips: async (params?: {
    status?: string;
    job_id?: string;
    min_score?: number;
    search?: string;
  }): Promise<Clip[]> => {
    const query = new URLSearchParams();
    if (params?.status && params.status !== 'all') query.set('status', params.status);
    if (params?.job_id) query.set('job_id', params.job_id);
    if (params?.min_score) query.set('min_score', params.min_score.toString());
    if (params?.search) query.set('search', params.search);

    const res = await fetch(`/api/clips?${query.toString()}`, { headers: getHeaders() });
    if (!res.ok) throw new Error('Failed to load clips');
    return res.json();
  },

  getClip: async (clipId: string): Promise<Clip> => {
    const res = await fetch(`/api/clips/${clipId}`, { headers: getHeaders() });
    if (!res.ok) throw new Error('Clip not found');
    return res.json();
  },

  updateClip: async (clipId: string, updates: Partial<Clip>): Promise<any> => {
    const res = await fetch(`/api/clips/${clipId}`, {
      method: 'PATCH',
      headers: getHeaders(),
      body: JSON.stringify(updates),
    });
    if (!res.ok) throw new Error('Failed to update clip');
    return res.json();
  },

  postClip: async (clipId: string): Promise<any> => {
    const res = await fetch(`/api/clips/${clipId}/post`, {
      method: 'POST',
      headers: getHeaders(),
    });
    if (!res.ok) throw new Error('Failed to approve clip for posting');
    return res.json();
  },

  // Notifications
  getNotifications: async (unreadOnly = false): Promise<NotificationItem[]> => {
    const res = await fetch(`/api/notifications?unread_only=${unreadOnly}`, { headers: getHeaders() });
    if (!res.ok) throw new Error('Failed to load notifications');
    return res.json();
  },

  markNotificationRead: async (notifId: string): Promise<any> => {
    const res = await fetch(`/api/notifications/${notifId}/read`, {
      method: 'PATCH',
      headers: getHeaders(),
    });
    if (!res.ok) throw new Error('Failed to mark notification read');
    return res.json();
  },

  // Instagram
  getInstagramHealth: async (): Promise<InstagramHealth> => {
    const res = await fetch('/api/instagram/health', { headers: getHeaders() });
    if (!res.ok) throw new Error('Failed to get Instagram status');
    return res.json();
  },
};

