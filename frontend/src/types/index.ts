export interface Task {
  id: string;
  description: string;
  scheduled_time: Date | null;
  is_completed: boolean;
  reminder_sent: boolean;
  call_sid?: string;
  created_at: Date;
}

export interface CallLog {
  id: string;
  call_sid: string;
  direction: "outbound" | "inbound";
  status: string;
  timestamp: Date;
  recording_url?: string;
}

export interface SipCredentials {
  username: string;
  password?: string;
  domain?: string;
  sip_uri?: string;
}

export interface UserProfile {
  id: string;
  email: string;
  timezone: string;
  sip_username?: string;
  sip_password?: string;
  sip_uri?: string;
  created_at?: Date;
}
