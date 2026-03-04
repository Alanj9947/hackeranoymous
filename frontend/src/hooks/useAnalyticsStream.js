import { useEffect, useState, useCallback, useRef } from 'react';

/**
 * Hook for connecting to analytics WebSocket stream.
 * Provides real-time metric updates every 30 seconds.
 */
export function useAnalyticsStream(companyId) {
  const [metrics, setMetrics] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [predictions, setPredictions] = useState(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState(null);
  const wsRef = useRef(null);

  const connect = useCallback(() => {
    if (!companyId) return;

    try {
      // Determine protocol (ws vs wss)
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/api/v1/ws/analytics/${companyId}`;

      wsRef.current = new WebSocket(wsUrl);
      wsRef.current.binaryType = 'arraybuffer';

      wsRef.current.onopen = () => {
        console.log('Analytics WebSocket connected');
        setConnected(true);
        setError(null);
      };

      wsRef.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);

          switch (message.type) {
            case 'metrics_update':
              setMetrics(message.data);
              break;

            case 'alert':
              setAlerts(prev => [...prev, {
                id: Date.now(),
                ...message.data,
                timestamp: message.timestamp
              }]);
              // Remove alerts after 5 seconds
              setTimeout(() => {
                setAlerts(prev => prev.slice(1));
              }, 5000);
              break;

            case 'prediction_update':
              setPredictions(message.data);
              break;

            case 'heartbeat':
              // Just acknowledge heartbeat
              break;

            case 'pong':
              // Pong response
              break;

            default:
              console.log('Unknown message type:', message.type);
          }
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
        }
      };

      wsRef.current.onerror = (event) => {
        console.error('Analytics WebSocket error:', event);
        setError('Connection error');
        setConnected(false);
      };

      wsRef.current.onclose = () => {
        console.log('Analytics WebSocket closed');
        setConnected(false);
        // Attempt reconnect after 3 seconds
        setTimeout(() => {
          if (companyId) {
            connect();
          }
        }, 3000);
      };
    } catch (err) {
      console.error('Failed to connect to analytics WebSocket:', err);
      setError(err.message);
      setConnected(false);
    }
  }, [companyId]);

  useEffect(() => {
    connect();

    return () => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  const requestUpdate = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send('update:now');
    }
  }, []);

  const ping = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send('ping');
    }
  }, []);

  return {
    metrics,
    alerts,
    predictions,
    connected,
    error,
    requestUpdate,
    ping
  };
}
