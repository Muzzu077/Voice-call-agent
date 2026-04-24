"use client";

import Link from "next/link";

const features = [
  {
    icon: "🧠",
    title: "Agent Brain",
    desc: "LLM reasoning with tool-calling, memory, and personality customization.",
  },
  {
    icon: "📞",
    title: "Voice Calls",
    desc: "Real-time Twilio integration with STT, TTS, and barge-in support.",
  },
  {
    icon: "🖥️",
    title: "Desktop Control",
    desc: "Open apps, search the web, type text, press keys — all by voice.",
  },
  {
    icon: "🔒",
    title: "Safety Layer",
    desc: "Three-tier action validation: Safe, Confirm, Blocked. You stay in control.",
  },
  {
    icon: "📊",
    title: "Full Observability",
    desc: "Track conversations, actions, latency, and errors in a live dashboard.",
  },
  {
    icon: "🧩",
    title: "Multi-Agent",
    desc: "Create unlimited agents, each with its own personality, voice, and tools.",
  },
];

const pricing = [
  {
    name: "Starter",
    price: "$0",
    period: "forever",
    features: [
      "2 Agents",
      "100 call minutes/mo",
      "Basic automation",
      "Community support",
    ],
    cta: "Get Started",
    highlighted: false,
  },
  {
    name: "Pro",
    price: "$29",
    period: "/month",
    features: [
      "20 Agents",
      "500 call minutes/mo",
      "Full automation",
      "Priority support",
      "API access",
    ],
    cta: "Start Free Trial",
    highlighted: true,
  },
  {
    name: "Business",
    price: "$99",
    period: "/month",
    features: [
      "Unlimited agents",
      "Unlimited minutes",
      "Custom integrations",
      "Dedicated support",
      "SLA guarantee",
    ],
    cta: "Contact Sales",
    highlighted: false,
  },
];

export default function LandingPage() {
  return (
    <div className="animated-gradient min-h-screen">
      {/* ── Navbar ─────────────────────────── */}
      <nav
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "16px 40px",
          borderBottom: "1px solid var(--border)",
          background: "rgba(10,10,15,0.8)",
          backdropFilter: "blur(10px)",
          position: "sticky",
          top: 0,
          zIndex: 50,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <span style={{ fontSize: "1.5rem" }}>🤖</span>
          <span
            style={{ fontSize: "1.2rem", fontWeight: 800 }}
            className="gradient-text"
          >
            VoiceAgent AI
          </span>
        </div>

        <div style={{ display: "flex", gap: "12px" }}>
          <Link href="/login">
            <button className="btn-outline" style={{ padding: "8px 20px", fontSize: "0.85rem" }}>
              Log In
            </button>
          </Link>
          <Link href="/register">
            <button className="btn-glow" style={{ padding: "8px 20px", fontSize: "0.85rem" }}>
              Get Started
            </button>
          </Link>
        </div>
      </nav>

      {/* ── Hero ───────────────────────────── */}
      <section
        style={{
          textAlign: "center",
          padding: "100px 20px 60px",
          maxWidth: "800px",
          margin: "0 auto",
        }}
      >
        <div
          style={{
            display: "inline-block",
            padding: "6px 16px",
            background: "rgba(99,102,241,0.15)",
            borderRadius: "20px",
            fontSize: "0.8rem",
            color: "#818cf8",
            fontWeight: 600,
            marginBottom: "20px",
          }}
        >
          🚀 AI that talks AND acts
        </div>

        <h1
          style={{
            fontSize: "3.5rem",
            fontWeight: 900,
            lineHeight: 1.1,
            marginBottom: "20px",
          }}
        >
          Build AI Agents That{" "}
          <span className="gradient-text">Talk, Call & Automate</span>
        </h1>

        <p
          style={{
            fontSize: "1.15rem",
            color: "var(--text-secondary)",
            lineHeight: 1.7,
            marginBottom: "36px",
            maxWidth: "600px",
            margin: "0 auto 36px",
          }}
        >
          Create voice agents that handle phone calls, control your desktop, execute workflows — all from a single platform.
        </p>

        <div style={{ display: "flex", gap: "16px", justifyContent: "center" }}>
          <Link href="/register">
            <button className="btn-glow" style={{ padding: "14px 36px", fontSize: "1.05rem" }}>
              Create Your Agent →
            </button>
          </Link>
          <a href="#features">
            <button className="btn-outline" style={{ padding: "14px 36px", fontSize: "1.05rem" }}>
              See Features
            </button>
          </a>
        </div>

        {/* Architecture flow */}
        <div
          style={{
            marginTop: "60px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: "12px",
            flexWrap: "wrap",
            fontSize: "0.9rem",
            color: "var(--text-muted)",
          }}
        >
          {["Voice Input", "→", "STT (Whisper)", "→", "LLM (Ollama)", "→", "Tool Call", "→", "Desktop / Call / Task"].map(
            (item, i) => (
              <span
                key={i}
                style={
                  item === "→"
                    ? { color: "var(--accent)" }
                    : {
                        padding: "6px 14px",
                        background: "var(--bg-card)",
                        border: "1px solid var(--border)",
                        borderRadius: "8px",
                      }
                }
              >
                {item}
              </span>
            )
          )}
        </div>
      </section>

      {/* ── Features ───────────────────────── */}
      <section
        id="features"
        style={{
          padding: "80px 40px",
          maxWidth: "1100px",
          margin: "0 auto",
        }}
      >
        <h2
          style={{
            textAlign: "center",
            fontSize: "2rem",
            fontWeight: 800,
            marginBottom: "50px",
          }}
        >
          Everything You Need
        </h2>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
            gap: "20px",
          }}
        >
          {features.map((f, i) => (
            <div
              key={i}
              className="glass glass-hover"
              style={{ padding: "28px", transition: "all 0.3s ease" }}
            >
              <div style={{ fontSize: "2rem", marginBottom: "12px" }}>
                {f.icon}
              </div>
              <h3
                style={{
                  fontSize: "1.1rem",
                  fontWeight: 700,
                  marginBottom: "8px",
                }}
              >
                {f.title}
              </h3>
              <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem", lineHeight: 1.6 }}>
                {f.desc}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Pricing ────────────────────────── */}
      <section
        id="pricing"
        style={{
          padding: "80px 40px",
          maxWidth: "1000px",
          margin: "0 auto",
        }}
      >
        <h2
          style={{
            textAlign: "center",
            fontSize: "2rem",
            fontWeight: 800,
            marginBottom: "50px",
          }}
        >
          Simple Pricing
        </h2>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
            gap: "20px",
          }}
        >
          {pricing.map((plan, i) => (
            <div
              key={i}
              className="glass"
              style={{
                padding: "32px",
                textAlign: "center",
                border: plan.highlighted
                  ? "1px solid var(--accent)"
                  : "1px solid var(--border)",
                boxShadow: plan.highlighted
                  ? "0 0 30px var(--accent-glow)"
                  : "none",
                position: "relative",
              }}
            >
              {plan.highlighted && (
                <div
                  style={{
                    position: "absolute",
                    top: "-12px",
                    left: "50%",
                    transform: "translateX(-50%)",
                    background: "var(--accent)",
                    color: "white",
                    padding: "4px 16px",
                    borderRadius: "20px",
                    fontSize: "0.75rem",
                    fontWeight: 700,
                  }}
                >
                  POPULAR
                </div>
              )}
              <h3
                style={{
                  fontSize: "1.1rem",
                  fontWeight: 700,
                  marginBottom: "8px",
                }}
              >
                {plan.name}
              </h3>
              <div style={{ marginBottom: "20px" }}>
                <span style={{ fontSize: "2.5rem", fontWeight: 900 }}>
                  {plan.price}
                </span>
                <span
                  style={{
                    color: "var(--text-muted)",
                    fontSize: "0.9rem",
                  }}
                >
                  {plan.period}
                </span>
              </div>
              <ul
                style={{
                  listStyle: "none",
                  padding: 0,
                  marginBottom: "24px",
                  textAlign: "left",
                }}
              >
                {plan.features.map((f, j) => (
                  <li
                    key={j}
                    style={{
                      padding: "8px 0",
                      fontSize: "0.9rem",
                      color: "var(--text-secondary)",
                      borderBottom: "1px solid rgba(42,42,58,0.3)",
                    }}
                  >
                    ✓ {f}
                  </li>
                ))}
              </ul>
              <Link href="/register">
                <button
                  className={plan.highlighted ? "btn-glow" : "btn-outline"}
                  style={{ width: "100%" }}
                >
                  {plan.cta}
                </button>
              </Link>
            </div>
          ))}
        </div>
      </section>

      {/* ── Footer ─────────────────────────── */}
      <footer
        style={{
          textAlign: "center",
          padding: "40px 20px",
          borderTop: "1px solid var(--border)",
          color: "var(--text-muted)",
          fontSize: "0.85rem",
        }}
      >
        © 2026 VoiceAgent AI. Built with passion.
      </footer>
    </div>
  );
}
