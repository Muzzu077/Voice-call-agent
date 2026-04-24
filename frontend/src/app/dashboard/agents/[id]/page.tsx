"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  getAgent,
  updateAgent,
  deleteAgent,
  getConversations,
  getActions,
} from "@/lib/api";

export default function AgentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const agentId = params.id as string;

  const [agent, setAgent] = useState<any>(null);
  const [conversations, setConversations] = useState<any[]>([]);
  const [actions, setActions] = useState<any[]>([]);
  const [tab, setTab] = useState<"overview" | "conversations" | "actions" | "settings">("overview");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      getAgent(agentId),
      getConversations(agentId).catch(() => []),
      getActions(agentId).catch(() => []),
    ])
      .then(([ag, convs, acts]) => {
        setAgent(ag);
        setConversations(convs);
        setActions(acts);
      })
      .catch(() => router.push("/dashboard"))
      .finally(() => setLoading(false));
  }, [agentId, router]);

  const handleDelete = async () => {
    if (!confirm("Are you sure you want to delete this agent?")) return;
    try {
      await deleteAgent(agentId);
      router.push("/dashboard/agents");
    } catch {}
  };

  if (loading || !agent) {
    return <p style={{ color: "var(--text-muted)" }}>Loading agent...</p>;
  }

  const tabs = [
    { key: "overview", label: "Overview", icon: "📊" },
    { key: "conversations", label: "Conversations", icon: "💬" },
    { key: "actions", label: "Actions", icon: "⚡" },
    { key: "settings", label: "Settings", icon: "⚙️" },
  ];

  return (
    <div>
      {/* ── Header ────────────────────────── */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: "32px",
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <h1 style={{ fontSize: "1.8rem", fontWeight: 800 }}>
              {agent.name}
            </h1>
            <span
              className={`badge ${agent.is_active ? "badge-success" : "badge-error"}`}
            >
              {agent.is_active ? "Active" : "Inactive"}
            </span>
          </div>
          <p style={{ color: "var(--text-secondary)", marginTop: "4px", fontSize: "0.9rem" }}>
            Voice: {agent.voice} · {(agent.tools_enabled || []).length} tools enabled
          </p>
        </div>
      </div>

      {/* ── Tabs ──────────────────────────── */}
      <div
        style={{
          display: "flex",
          gap: "4px",
          marginBottom: "28px",
          borderBottom: "1px solid var(--border)",
          paddingBottom: "0",
        }}
      >
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key as any)}
            style={{
              padding: "10px 18px",
              background: "transparent",
              border: "none",
              borderBottom: tab === t.key ? "2px solid var(--accent)" : "2px solid transparent",
              color: tab === t.key ? "var(--text-primary)" : "var(--text-muted)",
              fontSize: "0.9rem",
              fontWeight: tab === t.key ? 600 : 400,
              cursor: "pointer",
              transition: "all 0.2s ease",
            }}
          >
            {t.icon} {t.label}
          </button>
        ))}
      </div>

      {/* ── Overview Tab ──────────────────── */}
      {tab === "overview" && (
        <div>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
              gap: "16px",
              marginBottom: "32px",
            }}
          >
            <div className="stat-card">
              <div className="stat-value gradient-text">
                {conversations.length}
              </div>
              <div className="stat-label">Conversations</div>
            </div>
            <div className="stat-card">
              <div className="stat-value" style={{ color: "var(--success)" }}>
                {actions.filter((a: any) => a.status === "success").length}
              </div>
              <div className="stat-label">Successful Actions</div>
            </div>
            <div className="stat-card">
              <div className="stat-value" style={{ color: "var(--error)" }}>
                {actions.filter((a: any) => a.status === "failed").length}
              </div>
              <div className="stat-label">Failed Actions</div>
            </div>
          </div>

          {/* Personality display */}
          <div className="glass" style={{ padding: "24px", marginBottom: "20px" }}>
            <h3 style={{ fontSize: "1rem", fontWeight: 700, marginBottom: "12px" }}>
              🧠 Personality
            </h3>
            <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem", lineHeight: 1.6 }}>
              {agent.personality || "Default personality (Windows voice assistant with tool calling)"}
            </p>
          </div>

          {/* Tools display */}
          <div className="glass" style={{ padding: "24px" }}>
            <h3 style={{ fontSize: "1rem", fontWeight: 700, marginBottom: "12px" }}>
              🧩 Enabled Tools
            </h3>
            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
              {(agent.tools_enabled || []).map((tool: string) => (
                <span key={tool} className="badge badge-info" style={{ padding: "6px 14px" }}>
                  {tool}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ── Conversations Tab ─────────────── */}
      {tab === "conversations" && (
        <div>
          {conversations.length === 0 ? (
            <div className="glass" style={{ padding: "40px", textAlign: "center" }}>
              <p style={{ color: "var(--text-secondary)" }}>
                No conversations yet. Start talking to this agent!
              </p>
            </div>
          ) : (
            <div className="glass" style={{ overflow: "hidden" }}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>User Message</th>
                    <th>AI Response</th>
                    <th>Latency</th>
                    <th>Time</th>
                  </tr>
                </thead>
                <tbody>
                  {conversations.map((c: any, i: number) => (
                    <tr key={i}>
                      <td style={{ maxWidth: "250px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                        {c.user_message}
                      </td>
                      <td style={{ maxWidth: "250px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                        {c.ai_response}
                      </td>
                      <td>
                        {c.latency_ms ? (
                          <span className="badge badge-success">{c.latency_ms}ms</span>
                        ) : (
                          "—"
                        )}
                      </td>
                      <td style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                        {c.created_at ? new Date(c.created_at).toLocaleString() : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ── Actions Tab ───────────────────── */}
      {tab === "actions" && (
        <div>
          {actions.length === 0 ? (
            <div className="glass" style={{ padding: "40px", textAlign: "center" }}>
              <p style={{ color: "var(--text-secondary)" }}>
                No actions executed yet.
              </p>
            </div>
          ) : (
            <div className="glass" style={{ overflow: "hidden" }}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Action</th>
                    <th>Status</th>
                    <th>Result</th>
                    <th>Latency</th>
                    <th>Time</th>
                  </tr>
                </thead>
                <tbody>
                  {actions.map((a: any, i: number) => (
                    <tr key={i}>
                      <td>
                        <span className="badge badge-info">{a.action_type}</span>
                      </td>
                      <td>
                        <span
                          className={`badge ${
                            a.status === "success"
                              ? "badge-success"
                              : a.status === "blocked"
                              ? "badge-warning"
                              : "badge-error"
                          }`}
                        >
                          {a.status}
                        </span>
                      </td>
                      <td style={{ maxWidth: "200px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                        {a.result || "—"}
                      </td>
                      <td>{a.latency_ms ? `${a.latency_ms}ms` : "—"}</td>
                      <td style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                        {a.created_at ? new Date(a.created_at).toLocaleString() : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ── Settings Tab ──────────────────── */}
      {tab === "settings" && (
        <div style={{ maxWidth: "500px" }}>
          <div className="glass" style={{ padding: "24px", marginBottom: "20px" }}>
            <h3 style={{ fontSize: "1rem", fontWeight: 700, marginBottom: "16px" }}>
              Agent Configuration
            </h3>
            <div style={{ marginBottom: "16px" }}>
              <label style={{ display: "block", fontSize: "0.8rem", color: "var(--text-secondary)", marginBottom: "6px" }}>
                Agent ID
              </label>
              <input className="input-field" value={agent.id} readOnly style={{ opacity: 0.6 }} />
            </div>
            <div style={{ marginBottom: "16px" }}>
              <label style={{ display: "block", fontSize: "0.8rem", color: "var(--text-secondary)", marginBottom: "6px" }}>
                Name
              </label>
              <input className="input-field" value={agent.name} readOnly />
            </div>
          </div>

          <div className="glass" style={{ padding: "24px", borderColor: "var(--error)" }}>
            <h3 style={{ fontSize: "1rem", fontWeight: 700, marginBottom: "12px", color: "var(--error)" }}>
              Danger Zone
            </h3>
            <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginBottom: "16px" }}>
              Deleting an agent is permanent. All conversations and action logs will be lost.
            </p>
            <button
              onClick={handleDelete}
              style={{
                padding: "10px 20px",
                background: "rgba(239,68,68,0.15)",
                border: "1px solid var(--error)",
                borderRadius: "10px",
                color: "var(--error)",
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              Delete Agent
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
