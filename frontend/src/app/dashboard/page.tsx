"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { auth } from "../../lib/firebase";
import { signOut } from "firebase/auth";
import { useAuth } from "../../contexts/AuthContext";
import TaskList from "../../components/TaskList";
import CallLogList from "../../components/CallLogList";
import SipCredentials from "../../components/SipCredentials";
import LoadingSpinner from "../../components/LoadingSpinner";
import ScheduleChat from "../../components/ScheduleChat";

export default function DashboardPage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.push("/login");
    }
  }, [user, loading, router]);

  const handleLogout = async () => {
    try {
      await signOut(auth);
      router.push("/login");
    } catch (error) {
      console.error("Failed to log out", error);
    }
  };

  if (loading || !user) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="min-h-screen animated-gradient text-gray-100 p-4 sm:p-8 font-sans">
      <div className="max-w-7xl mx-auto space-y-8">
        
        {/* Header */}
        <header className="flex flex-col sm:flex-row justify-between items-center glass p-6 shadow-xl">
          <div className="mb-4 sm:mb-0">
            <h1 className="text-3xl font-extrabold gradient-text">
              Voice Call Dashboard
            </h1>
            <p className="text-gray-400 mt-1 font-medium">
              Welcome back, <span className="text-gray-200">{user.email}</span>
            </p>
          </div>
          <button
            onClick={handleLogout}
            className="btn-outline"
          >
            Sign Out
          </button>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Main Content: Tasks and Chat */}
          <main className="lg:col-span-2 space-y-6">
            <section className="glass p-6 shadow-xl">
              <div className="flex items-center gap-3 mb-6">
                <div className="bg-indigo-900/50 border border-indigo-500/30 p-2 rounded-lg text-indigo-400">
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
                  </svg>
                </div>
                <h2 className="text-2xl font-bold text-gray-100">Today&apos;s Tasks</h2>
              </div>
              <TaskList />
            </section>

            <ScheduleChat />
          </main>

          {/* Sidebar */}
          <aside className="space-y-8">
            <section className="glass-hover">
              <SipCredentials />
            </section>

            <section className="glass p-6 shadow-xl glass-hover">
              <div className="flex items-center gap-3 mb-6">
                <div className="bg-purple-900/50 border border-purple-500/30 p-2 rounded-lg text-purple-400">
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                  </svg>
                </div>
                <h2 className="text-xl font-bold text-gray-100">Call Logs</h2>
              </div>
              <CallLogList />
            </section>
          </aside>
          
        </div>
      </div>
    </div>
  );
}
