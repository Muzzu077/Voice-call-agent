import React, { useEffect, useState } from "react";
import { collection, query, orderBy, onSnapshot } from "firebase/firestore";
import { db } from "../lib/firebase";
import { CallLog } from "../types";
import { useAuth } from "../contexts/AuthContext";
import LoadingSpinner from "./LoadingSpinner";

export const CallLogList = () => {
  const { user } = useAuth();
  const [logs, setLogs] = useState<CallLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user) return;

    const logsRef = collection(db, "users", user.uid, "call_logs");
    const q = query(logsRef, orderBy("timestamp", "desc"));

    const unsubscribe = onSnapshot(q, (snapshot) => {
      const logsData: CallLog[] = [];
      snapshot.forEach((doc) => {
        const data = doc.data();
        logsData.push({
          id: doc.id,
          call_sid: data.call_sid,
          direction: data.direction,
          status: data.status,
          timestamp: data.timestamp?.toDate() || new Date(),
          recording_url: data.recording_url,
        });
      });
      setLogs(logsData);
      setLoading(false);
    }, (err) => {
      console.error("Error fetching call logs:", err);
      setError("Failed to load call logs");
      setLoading(false);
    });

    return () => unsubscribe();
  }, [user]);

  if (loading) return <LoadingSpinner />;
  if (error) return <div className="text-red-500">{error}</div>;

  if (logs.length === 0) {
    return <div className="text-gray-400 italic p-4 bg-gray-800/50 rounded-lg border border-gray-700">No call logs found.</div>;
  }

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case "completed": return "text-green-400 bg-green-900/30 border-green-800";
      case "failed":
      case "busy":
      case "no-answer": return "text-red-400 bg-red-900/30 border-red-800";
      case "in-progress":
      case "ringing": return "text-indigo-400 bg-indigo-900/30 border-indigo-800";
      default: return "text-gray-400 bg-gray-800 border-gray-700";
    }
  };

  return (
    <ul className="space-y-3">
      {logs.map((log) => (
        <li key={log.id} className="p-4 bg-gray-800/40 border border-gray-700 rounded-lg shadow-sm">
          <div className="flex justify-between items-start mb-2">
            <div>
              <span className="font-semibold text-gray-200 capitalize mr-2">
                {log.direction} Call
              </span>
              <span className={`text-xs px-2 py-1 rounded-full border ${getStatusColor(log.status)} capitalize`}>
                {log.status}
              </span>
            </div>
            <span className="text-sm text-gray-500">
              {log.timestamp.toLocaleString()}
            </span>
          </div>
          <div className="text-xs text-gray-500 mb-2 font-mono">
            SID: {log.call_sid}
          </div>
          {log.recording_url && (
            <div className="mt-3">
              <audio controls className="w-full h-8 opacity-80" src={log.recording_url}>
                Your browser does not support the audio element.
              </audio>
            </div>
          )}
        </li>
      ))}
    </ul>
  );
};

export default CallLogList;
