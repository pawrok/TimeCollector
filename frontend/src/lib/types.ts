export interface Tracker {
  id: number;
  name: string;
  color: string;
  sort_order: number;
  archived: boolean;
  created_at: string;
  is_running: boolean;
  running_since: string | null;
  today_completed_seconds: number;
  total_seconds: number;
}

export interface DailyStat {
  date: string;
  tracker_id: number;
  tracker_name: string;
  color: string;
  seconds: number;
}

export interface TotalStat {
  tracker_id: number;
  tracker_name: string;
  color: string;
  seconds: number;
}

export interface TrackerCreate {
  name: string;
  color?: string;
}

export interface TrackerUpdate {
  name?: string;
  color?: string;
  sort_order?: number;
  archived?: boolean;
}
