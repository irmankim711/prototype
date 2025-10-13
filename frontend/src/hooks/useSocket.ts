import { useEffect, useState } from "react";
import { io, Socket } from "socket.io-client";

type SubmissionEvent = { timestamp: number };
type ActivityEvent = { userId: number; action: string; timestamp: number };

export interface RealtimeData {
  submissions: SubmissionEvent[];
  activities: ActivityEvent[];
}

export function useSocket() {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [data, setData] = useState<RealtimeData>({ submissions: [], activities: [] });

  useEffect(() => {
    const s = io(import.meta.env.VITE_WS_URL || 'http://localhost:4001');
    setSocket(s);

    s.on('submission', (payload: SubmissionEvent) => {
      setData((d: any) => ({ ...d, submissions: [...d.submissions.slice(-99), payload] }));
    });

    s.on('activity', (payload: ActivityEvent) => {
      setData((d: any) => ({ ...d, activities: [...d.activities.slice(-99), payload] }));
    });

    return () => {
      s.disconnect();
    };
  }, []);

  return { socket, data };
}
