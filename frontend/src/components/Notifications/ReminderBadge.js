import React, { useState, useEffect, useCallback } from "react";
import { useAuth } from "../../context/AuthContext";
import { Badge } from "../ui/badge";
import { Bell } from "lucide-react";

export const ReminderBadge = () => {
  const { api } = useAuth();
  const [counts, setCounts] = useState({ total: 0, overdue: 0 });

  const fetchCounts = useCallback(async () => {
    try {
      const response = await api.get("/reminders?include_completed=false");
      const reminders = response.data || [];
      const now = new Date();
      
      const total = reminders.length;
      const overdue = reminders.filter(r => new Date(r.remind_at) < now).length;
      
      setCounts({ total, overdue });
    } catch (error) {
      console.log("Could not fetch reminder counts");
    }
  }, [api]);

  useEffect(() => {
    fetchCounts();
    // Refresh every 60 seconds
    const interval = setInterval(fetchCounts, 60000);
    return () => clearInterval(interval);
  }, [fetchCounts]);

  if (counts.total === 0) return null;

  return (
    <div className="relative inline-flex">
      {counts.overdue > 0 ? (
        <Badge 
          variant="destructive" 
          className="absolute -top-2 -right-2 h-5 min-w-[20px] flex items-center justify-center text-xs px-1 animate-pulse"
        >
          {counts.overdue}
        </Badge>
      ) : counts.total > 0 ? (
        <Badge 
          className="absolute -top-2 -right-2 h-5 min-w-[20px] flex items-center justify-center text-xs px-1 bg-amber-500"
        >
          {counts.total}
        </Badge>
      ) : null}
    </div>
  );
};

// Hook to get reminder counts for use in other components
export const useReminderCounts = () => {
  const { api } = useAuth();
  const [counts, setCounts] = useState({ total: 0, overdue: 0 });

  const fetchCounts = useCallback(async () => {
    try {
      const response = await api.get("/reminders?include_completed=false");
      const reminders = response.data || [];
      const now = new Date();
      
      const total = reminders.length;
      const overdue = reminders.filter(r => new Date(r.remind_at) < now).length;
      
      setCounts({ total, overdue });
    } catch (error) {
      console.log("Could not fetch reminder counts");
    }
  }, [api]);

  useEffect(() => {
    fetchCounts();
    const interval = setInterval(fetchCounts, 60000);
    return () => clearInterval(interval);
  }, [fetchCounts]);

  return counts;
};

export default ReminderBadge;
