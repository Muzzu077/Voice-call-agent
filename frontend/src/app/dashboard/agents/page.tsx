"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { listAgents } from "@/lib/api";

export default function AgentsListPage() {
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
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: "32px",
        }}
      >
        <div>
          <h1 style={{ fontSize: "1.8rem", fontWeight: 800 }}>Agents</h1>
          <p style={{ color: "var(--text-secondary)", marginTop: "4px" }}>
            Manage your AI voice agents.
          </p>
        </div>
        <Link href="/dashboard/agents/new">
          <button className="btn-glow" style={{ padding: "10px 24px" }}>
            + Create Agent
          </button>
        </Link>
      </div>

      {loading ? (
        <p style={{ color: "var(--text-muted)" }}>Loading...</p>
      ) : agents.length === 0 ? (
        <div
          className="glass"
          style={{ padding: "60px", textAlign: "center" }}
        >
          <p style={{ fontSize: "3rem", marginBottom: "16px" }}>🤖</p>
          <h2 style={{ fontWeight: 700, marginBottom: "8px" }}>
            No agents yet
          </h2>
          <p style={{ color: "var(--text-secondary)", marginBottom: "24px" }}>
            Create your first agent to get started with voice automation.
          </p>
          <Link href="/dashboard/agents/new">
            <button className="btn-glow">Create Your First Agent</button>
          </Link>
        </div>
      ) : (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
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
                style={{ padding: "24px", cursor: "pointer" }}
              >
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "flex-start",
                    marginBottom: "16px",
                  }}
                >
                  <div>
                    <h3 style={{ fontSize: "1.15rem", fontWeight: 700 }}>
                      {agent.name}
                    </h3>
                    <span
                      style={{
                        fontSize: "0.75rem",
                        color: "var(--text-muted)",
                      }}
                    >
                      Voice: {agent.voice || "default"}
                    </span>
                  </div>
                  <span
                    className={`badge ${
                      agent.is_active ? "badge-success" : "badge-error"
                    }`}
                  >
                    {agent.is_active ? "Active" : "Inactive"}
                  </span>
                </div>

                <p
                  style={{
                    color: "var(--text-secondary)",
                    fontSize: "0.85rem",
                    lineHeight: 1.5,
                    marginBottom: "16px",
                    display: "-webkit-box",
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: "vertical",
                    overflow: "hidden",
                  }}
                >
                  {agent.personality || "Default personality"}
                </p>

                <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
                  {(agent.tools_enabled || []).map((tool: string) => (
                    <span key={tool} className="badge badge-info">
                      {tool}
                    </span>
                  ))}
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
