import React, { useEffect, useState } from "react";
import { collection, query, orderBy, onSnapshot, doc, updateDoc } from "firebase/firestore";
import { db } from "../lib/firebase";
import { Task } from "../types";
import { useAuth } from "../contexts/AuthContext";
import LoadingSpinner from "./LoadingSpinner";

export const TaskList = () => {
  const { user } = useAuth();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user) return;

    const tasksRef = collection(db, "users", user.uid, "tasks");
    const q = query(tasksRef, orderBy("created_at", "desc"));

    const unsubscribe = onSnapshot(q, (snapshot) => {
      const tasksData: Task[] = [];
      snapshot.forEach((doc) => {
        const data = doc.data();
        tasksData.push({
          id: doc.id,
          description: data.description,
          scheduled_time: data.scheduled_time?.toDate() || null,
          is_completed: data.is_completed,
          reminder_sent: data.reminder_sent,
          call_sid: data.call_sid,
          created_at: data.created_at?.toDate() || new Date(),
        });
      });
      setTasks(tasksData);
      setLoading(false);
    }, (err) => {
      console.error("Error fetching tasks:", err);
      setError("Failed to load tasks");
      setLoading(false);
    });

    return () => unsubscribe();
  }, [user]);

  const toggleTaskCompletion = async (taskId: string, isCompleted: boolean) => {
    if (!user) return;
    try {
      const taskRef = doc(db, "users", user.uid, "tasks", taskId);
      await updateDoc(taskRef, { is_completed: !isCompleted });
    } catch (err) {
      console.error("Error updating task:", err);
    }
  };

  if (loading) return <LoadingSpinner />;
  if (error) return <div className="text-red-500">{error}</div>;

  if (tasks.length === 0) {
    return <div className="text-gray-400 italic p-4 bg-gray-800/50 rounded-lg border border-gray-700">No tasks found.</div>;
  }

  return (
    <ul className="space-y-2">
      {tasks.map((task) => (
        <li key={task.id} className="flex items-center gap-3 p-3 bg-gray-800/40 border border-gray-700 rounded-lg shadow-sm hover:shadow-md transition-shadow hover:border-gray-500">
          <input
            type="checkbox"
            checked={task.is_completed}
            onChange={() => toggleTaskCompletion(task.id, task.is_completed)}
            className="w-5 h-5 text-indigo-500 bg-gray-900 border-gray-600 rounded focus:ring-indigo-500 focus:ring-offset-gray-900"
          />
          <div className="flex-1">
            <span className={`block ${task.is_completed ? "line-through text-gray-500" : "text-gray-200"}`}>
              {task.description}
            </span>
            {task.scheduled_time && (
              <span className="text-xs text-gray-400">
                Scheduled for: {task.scheduled_time.toLocaleString()}
              </span>
            )}
          </div>
          {task.reminder_sent && (
            <span className="text-xs bg-green-900/30 text-green-400 border border-green-800 px-2 py-1 rounded-full whitespace-nowrap">
              Reminder Sent
            </span>
          )}
        </li>
      ))}
    </ul>
  );
};

export default TaskList;
