import { useEffect, useRef, useState, useCallback } from 'react';
import { useAuthStore } from '@/stores/auth-store';

interface CallEvent {
  type: 'call_started' | 'call_ended' | 'transcript_update' | 'extraction_complete' | 'error';
  call_id?: string;
  data?: Record<string, unknown>;
  timestamp?: string;
}

interface UseCallWebSocketOptions {
  callId?: string;
  onEvent?: (event: CallEvent) => void;
  enabled?: boolean;
}

export function useCallWebSocket({ callId, onEvent, enabled = true }: UseCallWebSocketOptions) {
  const [connected, setConnected] = useState(false);
  const [lastEvent, setLastEvent] = useState<CallEvent | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>();
  const token = useAuthStore((s) => s.accessToken);

  const connect = useCallback(() => {
    if (!callId || !enabled || !token) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/calls/${callId}?token=${token}`;

    try {
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as CallEvent;
          setLastEvent(data);
          onEvent?.(data);
        } catch {
          // non-JSON message
        }
      };

      ws.onclose = () => {
        setConnected(false);
        // Auto-reconnect after 3 seconds
        if (enabled) {
          reconnectTimer.current = setTimeout(connect, 3000);
        }
      };

      ws.onerror = () => {
        ws.close();
      };

      wsRef.current = ws;
    } catch {
      // WebSocket creation failed
    }
  }, [callId, enabled, token, onEvent]);

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, [connect]);

  const send = useCallback((data: Record<string, unknown>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  }, []);

  return { connected, lastEvent, send };
}
