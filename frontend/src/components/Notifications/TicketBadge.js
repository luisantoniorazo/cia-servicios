import { useState, useEffect, useCallback } from "react";
import { useAuth } from "../../context/AuthContext";

// Hook to get ticket counts with unread responses
export const useTicketCounts = () => {
  const { api, user } = useAuth();
  const [counts, setCounts] = useState({ total: 0, unread: 0 });

  const fetchCounts = useCallback(async () => {
    try {
      const response = await api.get("/tickets/unread-count");
      setCounts(response.data || { total: 0, unread: 0 });
    } catch (error) {
      console.log("Could not fetch ticket counts");
    }
  }, [api]);

  useEffect(() => {
    if (user) {
      fetchCounts();
      // Refresh every 30 seconds
      const interval = setInterval(fetchCounts, 30000);
      return () => clearInterval(interval);
    }
  }, [fetchCounts, user]);

  return counts;
};

export default useTicketCounts;
