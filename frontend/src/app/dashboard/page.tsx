"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { listAgents } from "@/lib/api";

export default function DashboardOverview() {
  const [agents, setAgents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listAgents()
      .then(setAgents)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <h1 style={{ fontSize: "1.8rem", fontWeight: 800, marginBottom: "8px" }}>
        Dashboard
      </h1>
      <p style={{ color: "var(--text-secondary)", marginBottom: "32px" }}>
        Overview of your AI voice agents and platform activity.
      </p>

      {/* ── Stats ────────────────────────── */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
          gap: "16px",
          marginBottom: "40px",
        }}
      >
        <div className="stat-card">
          <div className="stat-value gradient-text">{agents.length}</div>
          <div className="stat-label">Active Agents</div>
        </div>
        <div className="stat-card">
          <div className="stat-value" style={{ color: "var(--success)" }}>
            —
          </div>
          <div className="stat-label">Calls Today</div>
        </div>
        <div className="stat-card">
          <div className="stat-value" style={{ color: "var(--warning)" }}>
            —
          </div>
          <div className="stat-label">Actions Executed</div>
        </div>
        <div className="stat-card">
          <div className="stat-value" style={{ color: "#06b6d4" }}>
            —
          </div>
          <div className="stat-label">Avg Latency</div>
        </div>
      </div>

      {/* ── Agent List ───────────────────── */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: "20px",
        }}
      >
        <h2 style={{ fontSize: "1.2rem", fontWeight: 700 }}>Your Agents</h2>
        <Link href="/dashboard/agents/new">
          <button className="btn-glow" style={{ padding: "8px 20px", fontSize: "0.85rem" }}>
            + New Agent
          </button>
        </Link>
      </div>

      {loading ? (
        <p style={{ color: "var(--text-muted)" }}>Loading agents...</p>
      ) : agents.length === 0 ? (
        <div
          className="glass"
          style={{
            padding: "48px",
            textAlign: "center",
          }}
        >
          <p style={{ fontSize: "2rem", marginBottom: "12px" }}>🤖</p>
          <p style={{ color: "var(--text-secondary)", marginBottom: "20px" }}>
            No agents yet. Create your first AI voice agent!
          </p>
          <Link href="/dashboard/agents/new">
            <button className="btn-glow">Create Agent</button>
          </Link>
        </div>
      ) : (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
            gap: "16px",
          }}
        >
          {agents.map((agent: any) => (
            <Link
              key={agent.id}
              href={`/dashboard/agents/${agent.id}`}
              style={{ textDecoration: "none", color: "inherit" }}
            >
              <div
                className="glass glass-hover"
                style={{
                  padding: "24px",
                  cursor: "pointer",
                  transition: "all 0.3s ease",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    marginBottom: "12px",
                  }}
                >
                  <h3 style={{ fontSize: "1.1rem", fontWeight: 700 }}>
                    {agent.name}
                  </h3>
                  <span className={`badge ${agent.is_active ? "badge-success" : "badge-error"}`}>
                    {agent.is_active ? "Active" : "Inactive"}
                  </span>
                </div>
                <p
                  style={{
                    color: "var(--text-secondary)",
                    fontSize: "0.85rem",
                    marginBottom: "12px",
                    display: "-webkit-box",
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: "vertical",
                    overflow: "hidden",
                  }}
                >
                  {agent.personality || "Default personality"}
                </p>
                <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
                  {(agent.tools_enabled || []).slice(0, 3).map((tool: string) => (
                    <span key={tool} className="badge badge-info">
                      {tool}
                    </span>
                  ))}
                  {(agent.tools_enabled || []).length > 3 && (
                    <span className="badge badge-info">
                      +{agent.tools_enabled.length - 3}
                    </span>
                  )}
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
