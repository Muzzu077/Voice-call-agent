"use client";

import React, { useState, useRef, useEffect } from "react";
import { auth } from "../lib/firebase";
import LoadingSpinner from "./LoadingSpinner";

interface Message {
  sender: "user" | "assistant";
  text: string;
  timestamp: Date;
  extractedTasks?: Array<{
    id: string;
    description: string;
    scheduled_time: string | null;
  }>;
}

export const ScheduleChat = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      sender: "assistant",
      text: "Hello! I am your AI Schedule Assistant. Paste or type your list of tasks, meetings, or study blocks here (e.g., 'Study AI neural networks today at 3:30 PM, then hit the gym at 7 PM'), and I will parse and add them to your task list.",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userText = input.trim();
    setInput("");
    setLoading(true);

    // Add user message to state
    setMessages((prev) => [
      ...prev,
      {
        sender: "user",
        text: userText,
        timestamp: new Date(),
      },
    ]);

    try {
      const user = auth.currentUser;
      if (!user) {
        throw new Error("You must be logged in to schedule tasks.");
      }

      const idToken = await user.getIdToken();
      
      // Determine functions base URL dynamically
      const functionsUrl = 
        typeof window !== "undefined" && window.location.hostname === "localhost"
          ? "http://127.0.0.1:5001/demo-project/us-central1"
          : process.env.NEXT_PUBLIC_FUNCTIONS_URL || `https://us-central1-${process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID}.cloudfunctions.net`;

      const response = await fetch(`${functionsUrl}/parse_text_tasks`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${idToken}`,
        },
        body: JSON.stringify({ text: userText }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `HTTP error ${response.status}`);
      }

      const data = await response.json();
      
      if (data.success) {
        const tasksCount = data.tasks.length;
        let reply = `I have successfully extracted and added ${tasksCount} task${tasksCount === 1 ? "" : "s"} to your dashboard!`;
        if (tasksCount === 0) {
          reply = "I listened but couldn't detect any specific tasks with times in your message. Try being more specific with hours (e.g. 15:30 or 3 PM).";
        }
        
        setMessages((prev) => [
          ...prev,
          {
            sender: "assistant",
            text: reply,
            timestamp: new Date(),
            extractedTasks: data.tasks,
          },
        ]);
      } else {
        throw new Error("Failed parsing schedule tasks.");
      }
    } catch (err: any) {
      console.error("Chat error:", err);
      setMessages((prev) => [
        ...prev,
        {
          sender: "assistant",
          text: `Error: ${err.message || "An unexpected error occurred while communicating with the assistant."}`,
          timestamp: new Date(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass border border-gray-700 rounded-lg shadow-sm overflow-hidden flex flex-col h-[480px]">
      {/* Header */}
      <div className="px-4 py-4 sm:px-6 bg-gray-800/60 border-b border-gray-700 flex items-center gap-3">
        <div className="bg-indigo-900/50 border border-indigo-500/30 p-2 rounded-lg text-indigo-400">
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
        </div>
        <div>
          <h3 className="text-lg leading-6 font-medium text-gray-100">Schedule Assistant Chat</h3>
          <p className="text-xs text-gray-400">Quickly type tasks and schedules to add them to your planner</p>
        </div>
      </div>

      {/* Messages List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-900/20">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.sender === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm shadow-md transition-all ${
                msg.sender === "user"
                  ? "bg-indigo-600 text-white rounded-br-none"
                  : "bg-gray-800/80 text-gray-200 border border-gray-700 rounded-bl-none"
              }`}
            >
              <p className="leading-relaxed">{msg.text}</p>
              
              {/* Render Extracted Tasks if present */}
              {msg.extractedTasks && msg.extractedTasks.length > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-700/60 space-y-2">
                  <span className="text-xs font-semibold text-indigo-300 block uppercase tracking-wider">
                    Extracted Tasks:
                  </span>
                  <ul className="space-y-1.5">
                    {msg.extractedTasks.map((t, tIdx) => (
                      <li key={t.id || tIdx} className="flex items-start gap-2 bg-gray-900/50 p-2 rounded border border-gray-800">
                        <svg className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <div className="flex-1">
                          <span className="font-medium text-gray-100 block">{t.description}</span>
                          {t.scheduled_time && (
                            <span className="text-xxs text-gray-400 font-mono">
                              {new Date(t.scheduled_time).toLocaleString()}
                            </span>
                          )}
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <span className={`block text-[10px] mt-1.5 text-right ${msg.sender === "user" ? "text-indigo-200" : "text-gray-400"}`}>
                {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-800/80 border border-gray-700 text-gray-200 rounded-2xl rounded-bl-none px-4 py-3 shadow-md flex items-center gap-2">
              <LoadingSpinner size="sm" />
              <span className="text-xs text-gray-400 italic">Assistant is parsing schedule...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Form */}
      <form onSubmit={handleSend} className="p-3 border-t border-gray-700 bg-gray-800/40 flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="e.g. Schedule database audit for 2 PM today"
          disabled={loading}
          className="input-field py-2 text-sm flex-1 bg-gray-900 border-gray-700"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="btn-glow py-2 px-5 flex items-center justify-center text-sm font-semibold rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Send
        </button>
      </form>
    </div>
  );
};

export default ScheduleChat;
