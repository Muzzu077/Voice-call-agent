"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createAgent } from "@/lib/api";

const ALL_TOOLS = [
  { id: "open_app", label: "Open App", icon: "🚀" },
  { id: "search_browser", label: "Browser Search", icon: "🔍" },
  { id: "open_url", label: "Open URL", icon: "🌐" },
  { id: "create_task", label: "Create Task", icon: "📝" },
  { id: "create_reminder", label: "Create Reminder", icon: "⏰" },
  { id: "save_note", label: "Save Note", icon: "📋" },
  { id: "make_call", label: "Make Call", icon: "📞" },
  { id: "type_text", label: "Type Text", icon: "⌨️" },
  { id: "press_key", label: "Press Key", icon: "🔑" },
  { id: "click_screen", label: "Click Screen", icon: "🖱️" },
];

export default function NewAgentPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [personality, setPersonality] = useState("");
  const [voice, setVoice] = useState("default");
  const [tools, setTools] = useState<string[]>(["open_app", "search_browser", "create_task", "create_reminder"]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const toggleTool = (toolId: string) => {
    setTools((prev) =>
      prev.includes(toolId)
        ? prev.filter((t) => t !== toolId)
        : [...prev, toolId]
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!name.trim()) {
      setError("Agent name is required");
      return;
    }

    setLoading(true);

    try {
      const agent = await createAgent({
        name: name.trim(),
        personality: personality.trim() || undefined,
        voice,
        tools_enabled: tools,
      });
      router.push(`/dashboard/agents/${agent.id}`);
    } catch (err: any) {
      setError(err.message || "Failed to create agent");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: "680px" }}>
      <h1 style={{ fontSize: "1.8rem", fontWeight: 800, marginBottom: "8px" }}>
        Create New Agent
      </h1>
      <p style={{ color: "var(--text-secondary)", marginBottom: "32px" }}>
        Configure your AI voice agent&apos;s personality, voice, and capabilities.
      </p>

      <form onSubmit={handleSubmit}>
        {/* Name */}
        <div style={{ marginBottom: "24px" }}>
          <label style={{ display: "block", fontSize: "0.85rem", fontWeight: 600, marginBottom: "8px" }}>
            Agent Name *
          </label>
          <input
            className="input-field"
            placeholder="e.g. Office Assistant, Sales Bot, Desktop Helper"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
        </div>

        {/* Personality */}
        <div style={{ marginBottom: "24px" }}>
          <label style={{ display: "block", fontSize: "0.85rem", fontWeight: 600, marginBottom: "8px" }}>
            Personality / System Prompt
          </label>
          <textarea
            className="input-field"
            placeholder="You are a professional assistant that helps manage desktop tasks..."
            value={personality}
            onChange={(e) => setPersonality(e.target.value)}
            rows={4}
            style={{ resize: "vertical", minHeight: "100px" }}
          />
          <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "6px" }}>
            Leave blank for default personality. This defines how your agent behaves on calls.
          </p>
        </div>

        {/* Voice */}
        <div style={{ marginBottom: "24px" }}>
          <label style={{ display: "block", fontSize: "0.85rem", fontWeight: 600, marginBottom: "8px" }}>
            Voice
          </label>
          <select
            className="input-field"
            value={voice}
            onChange={(e) => setVoice(e.target.value)}
            style={{ cursor: "pointer" }}
          >
            <option value="default">Default (Kokoro)</option>
            <option value="male_1">Male Voice 1</option>
            <option value="female_1">Female Voice 1</option>
          </select>
        </div>

        {/* Tools */}
        <div style={{ marginBottom: "32px" }}>
          <label style={{ display: "block", fontSize: "0.85rem", fontWeight: 600, marginBottom: "12px" }}>
            Enabled Tools
          </label>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))",
              gap: "10px",
            }}
          >
            {ALL_TOOLS.map((tool) => {
              const selected = tools.includes(tool.id);
              return (
                <div
                  key={tool.id}
                  onClick={() => toggleTool(tool.id)}
                  style={{
                    padding: "12px 14px",
                    borderRadius: "10px",
                    border: `1px solid ${selected ? "var(--accent)" : "var(--border)"}`,
                    background: selected ? "rgba(99,102,241,0.1)" : "var(--bg-card)",
                    cursor: "pointer",
                    transition: "all 0.2s ease",
                    display: "flex",
                    alignItems: "center",
                    gap: "8px",
                    fontSize: "0.85rem",
                  }}
                >
                  <span>{tool.icon}</span>
                  <span style={{ fontWeight: selected ? 600 : 400 }}>
                    {tool.label}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {error && (
          <p
            style={{
              color: "var(--error)",
              fontSize: "0.85rem",
              marginBottom: "16px",
            }}
          >
            {error}
          </p>
        )}

        <div style={{ display: "flex", gap: "12px" }}>
          <button
            className="btn-glow"
            type="submit"
            disabled={loading}
            style={{ opacity: loading ? 0.7 : 1 }}
          >
            {loading ? "Creating..." : "Create Agent"}
          </button>
          <button
            className="btn-outline"
            type="button"
            onClick={() => router.back()}
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
