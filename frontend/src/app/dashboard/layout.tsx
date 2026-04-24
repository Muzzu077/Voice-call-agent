"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { isAuthenticated, clearToken, getMe } from "@/lib/api";

const navItems = [
  { href: "/dashboard", label: "Overview", icon: "📊" },
  { href: "/dashboard/agents", label: "Agents", icon: "🤖" },
];

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push("/login");
      return;
    }
    getMe()
      .then(setUser)
      .catch(() => {
        clearToken();
        router.push("/login");
      });
  }, [router]);

  const handleLogout = () => {
    clearToken();
    router.push("/login");
  };

  if (!user) {
    return (
      <div
        style={{
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "var(--bg-primary)",
          color: "var(--text-secondary)",
        }}
      >
        Loading...
      </div>
    );
  }

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      {/* ── Sidebar ────────────────────────── */}
      <aside className="sidebar" style={{ padding: "20px 14px" }}>
        <Link
          href="/dashboard"
          style={{ textDecoration: "none" }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "10px",
              padding: "8px 12px",
              marginBottom: "32px",
            }}
          >
            <span style={{ fontSize: "1.4rem" }}>🤖</span>
            <span
              style={{ fontSize: "1.1rem", fontWeight: 800 }}
              className="gradient-text"
            >
              VoiceAgent
            </span>
          </div>
        </Link>

        <nav style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`sidebar-link ${
                pathname === item.href ? "active" : ""
              }`}
            >
              <span>{item.icon}</span>
              <span>{item.label}</span>
            </Link>
          ))}
        </nav>

        <div
          style={{
            position: "absolute",
            bottom: "20px",
            left: "14px",
            right: "14px",
          }}
        >
          <div
            style={{
              padding: "12px",
              background: "var(--bg-card)",
              borderRadius: "10px",
              border: "1px solid var(--border)",
            }}
          >
            <p
              style={{
                fontSize: "0.8rem",
                color: "var(--text-secondary)",
                marginBottom: "4px",
              }}
            >
              Signed in as
            </p>
            <p
              style={{
                fontSize: "0.85rem",
                fontWeight: 600,
                marginBottom: "10px",
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
              }}
            >
              {user.email}
            </p>
            <button
              onClick={handleLogout}
              style={{
                width: "100%",
                padding: "6px",
                background: "transparent",
                border: "1px solid var(--border)",
                borderRadius: "6px",
                color: "var(--text-secondary)",
                fontSize: "0.8rem",
                cursor: "pointer",
              }}
            >
              Sign Out
            </button>
          </div>
        </div>
      </aside>

      {/* ── Main Content ───────────────────── */}
      <main
        style={{
          flex: 1,
          padding: "32px 40px",
          overflowY: "auto",
          background: "var(--bg-primary)",
        }}
      >
        {children}
      </main>
    </div>
  );
}
