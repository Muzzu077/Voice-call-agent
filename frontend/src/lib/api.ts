const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ── Auth Token Management ─────────────────────────

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("voiceagent_token");
}

export function setToken(token: string) {
  localStorage.setItem("voiceagent_token", token);
}

export function clearToken() {
  localStorage.removeItem("voiceagent_token");
}

export function isAuthenticated(): boolean {
  return !!getToken();
}

// ── Fetch Wrapper ─────────────────────────────────

async function apiFetch(
  path: string,
  options: RequestInit = {}
): Promise<Response> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (res.status === 401) {
    clearToken();
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
  }

  return res;
}

// ── Auth ──────────────────────────────────────────

export async function register(email: string, password: string) {
  const res = await apiFetch("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Registration failed");
  }
  return res.json();
}

export async function login(email: string, password: string) {
  const formData = new URLSearchParams();
  formData.append("username", email);
  formData.append("password", password);

  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: formData.toString(),
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Login failed");
  }

  const data = await res.json();
  setToken(data.access_token);
  return data;
}

export async function getMe() {
  const res = await apiFetch("/auth/me");
  if (!res.ok) throw new Error("Not authenticated");
  return res.json();
}

// ── Agents ────────────────────────────────────────

export interface AgentConfig {
  name: string;
  personality?: string;
  voice?: string;
  tools_enabled?: string[];
}

export async function createAgent(config: AgentConfig) {
  const res = await apiFetch("/agents", {
    method: "POST",
    body: JSON.stringify(config),
  });
  if (!res.ok) throw new Error("Failed to create agent");
  return res.json();
}

export async function listAgents() {
  const res = await apiFetch("/agents");
  if (!res.ok) throw new Error("Failed to list agents");
  return res.json();
}

export async function getAgent(id: string) {
  const res = await apiFetch(`/agents/${id}`);
  if (!res.ok) throw new Error("Agent not found");
  return res.json();
}

export async function updateAgent(id: string, config: Partial<AgentConfig>) {
  const res = await apiFetch(`/agents/${id}`, {
    method: "PUT",
    body: JSON.stringify(config),
  });
  if (!res.ok) throw new Error("Failed to update agent");
  return res.json();
}

export async function deleteAgent(id: string) {
  const res = await apiFetch(`/agents/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error("Failed to delete agent");
}

// ── Conversations ─────────────────────────────────

export async function getConversations(agentId: string, page = 1, limit = 20) {
  const res = await apiFetch(
    `/agents/${agentId}/conversations?page=${page}&limit=${limit}`
  );
  if (!res.ok) return [];
  return res.json();
}

// ── Actions ───────────────────────────────────────

export async function getActions(agentId: string, page = 1, limit = 20) {
  const res = await apiFetch(
    `/agents/${agentId}/actions?page=${page}&limit=${limit}`
  );
  if (!res.ok) return [];
  return res.json();
}

// ── Stats ─────────────────────────────────────────

export async function getAgentStats(agentId: string) {
  const res = await apiFetch(`/agents/${agentId}/stats`);
  if (!res.ok) return null;
  return res.json();
}

// ── Chat ──────────────────────────────────────────

export async function sendChat(message: string) {
  const res = await apiFetch("/chat", {
    method: "POST",
    body: JSON.stringify({ message }),
  });
  if (!res.ok) throw new Error("Chat failed");
  return res.json();
}
