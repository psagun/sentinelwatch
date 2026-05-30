import { useEffect, useRef } from 'react';

export function useSSE<T>(
  url: string,
  onMessage: (data: T) => void,
  enabled = true,
) {
  const cb = useRef(onMessage);
  cb.current = onMessage;

  useEffect(() => {
    if (!enabled) return;

    const evtSource = new EventSource(`/api${url}`);
    evtSource.onmessage = (e) => {
      try {
        const parsed = JSON.parse(e.data) as T;
        cb.current(parsed);
      } catch {
        // ignore parse errors
      }
    };
    evtSource.onerror = () => {
      // reconnect automatically
    };

    return () => evtSource.close();
  }, [url, enabled]);
}
