/**
 * useConversation Hook - Real-time conversation with AI agent
 * Handles WebSocket connection, audio recording, and message management
 */

import { useState, useCallback, useRef, useEffect } from 'react';

export const useConversation = (agentId) => {
  // State
  const [isConnected, setIsConnected] = useState(false);
  const [transcript, setTranscript] = useState([]);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [error, setError] = useState(null);
  const [callDuration, setCallDuration] = useState(0);

  // Refs
  const wsRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const streamRef = useRef(null);
  const audioContextRef = useRef(null);
  const callStartTimeRef = useRef(null);
  const timerIntervalRef = useRef(null);
  const conversationIdRef = useRef(null);

  // Get WebSocket URL based on environment
  const getWsUrl = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    let apiUrl = import.meta.env.VITE_API_URL || `${protocol}//${host}`;
    
    // Replace http:// with ws:// or https:// with wss://
    apiUrl = apiUrl.replace(/^https?:\/\//, '');
    
    return `${protocol}//${apiUrl}/api/v1/ws/talk-to-agent/${agentId}`;
  }, [agentId]);

  // Start recording audio
  const startRecording = useCallback(async () => {
    try {
      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 16000,
        },
      });

      streamRef.current = stream;
      setIsListening(true);
      setError(null);

      // Create MediaRecorder
      const options = {
        mimeType: 'audio/webm;codecs=opus',
        audioBitsPerSecond: 16000,
      };

      const mediaRecorder = new MediaRecorder(stream, options);
      mediaRecorderRef.current = mediaRecorder;

      // Send audio chunks as they're recorded
      mediaRecorder.addEventListener('dataavailable', (event) => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN && event.data.size > 0) {
          wsRef.current.send(event.data);
        }
      });

      mediaRecorder.addEventListener('error', (error) => {
        console.error('MediaRecorder error:', error);
        setError('Error recording audio');
      });

      // Start recording with 500ms time slices
      mediaRecorder.start(500);
      console.log('Recording started');
    } catch (err) {
      const errorMsg = err.name === 'NotAllowedError'
        ? 'Microphone access denied'
        : 'Error accessing microphone';
      console.error('Microphone error:', err);
      setError(errorMsg);
      setIsListening(false);
    }
  }, []);

  // Stop recording
  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    setIsListening(false);
    console.log('Recording stopped');
  }, []);

  // Play audio response from server
  const playAudio = useCallback((audioData) => {
    try {
      setIsSpeaking(true);

      if (!audioContextRef.current) {
        audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
      }

      const audioContext = audioContextRef.current;

      // Decode audio data
      audioContext.decodeAudioData(
        audioData,
        (audioBuffer) => {
          const source = audioContext.createBufferSource();
          source.buffer = audioBuffer;
          source.connect(audioContext.destination);

          source.onended = () => {
            setIsSpeaking(false);
          };

          source.start(0);
        },
        (err) => {
          console.error('Error decoding audio:', err);
          setIsSpeaking(false);
          setError('Error playing audio response');
        }
      );
    } catch (err) {
      console.error('Audio playback error:', err);
      setError('Error playing audio');
      setIsSpeaking(false);
    }
  }, []);

  // Handle WebSocket messages
  const handleMessage = useCallback(
    (event) => {
      if (event.data instanceof ArrayBuffer) {
        // Binary audio data - play it
        playAudio(event.data);
      } else if (typeof event.data === 'string') {
        try {
          const message = JSON.parse(event.data);

          switch (message.type) {
            case 'connected':
              console.log('Connected to agent:', message.agent_name);
              conversationIdRef.current = message.conversation_id;
              // Optionally add system message
              break;

            case 'transcript':
              console.log('Transcript:', message.speaker, message.text);
              setTranscript((prev) => [
                ...prev,
                {
                  speaker: message.speaker,
                  text: message.text,
                  timestamp: new Date().toISOString(),
                },
              ]);
              break;

            case 'status':
              console.log('Status:', message.message);
              if (message.processing) {
                setIsListening(false);
              }
              break;

            case 'error':
              console.error('Server error:', message.message);
              setError(message.message);
              break;

            default:
              console.log('Unknown message type:', message.type);
          }
        } catch (err) {
          console.error('Error parsing message:', err);
        }
      }
    },
    [playAudio]
  );

  // Start conversation
  const startConversation = useCallback(async () => {
    try {
      setError(null);
      setTranscript([]);
      callStartTimeRef.current = Date.now();

      const wsUrl = getWsUrl();
      console.log('Connecting to:', wsUrl);

      wsRef.current = new WebSocket(wsUrl);
      wsRef.current.binaryType = 'arraybuffer';

      wsRef.current.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        // Start recording (fire and forget)
        startRecording().catch((err) => {
          console.error('Error starting recording:', err);
          setError(err.message || 'Failed to start recording');
        });

        // Start call timer
        timerIntervalRef.current = setInterval(() => {
          const elapsed = Math.floor((Date.now() - callStartTimeRef.current) / 1000);
          setCallDuration(elapsed);
        }, 1000);
      };

      wsRef.current.onmessage = handleMessage;

      wsRef.current.onclose = () => {
        console.log('WebSocket closed');
        setIsConnected(false);
        stopRecording();
        if (timerIntervalRef.current) {
          clearInterval(timerIntervalRef.current);
        }
      };

      wsRef.current.onerror = (err) => {
        console.error('WebSocket error:', err);
        setError('Connection error');
      };
    } catch (err) {
      console.error('Error starting conversation:', err);
      setError(err.message || 'Failed to start conversation');
    }
  }, [getWsUrl, startRecording, stopRecording, handleMessage]);

  // End conversation
  const endConversation = useCallback(() => {
    stopRecording();

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    if (timerIntervalRef.current) {
      clearInterval(timerIntervalRef.current);
    }

    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }

    setIsConnected(false);
    setIsListening(false);
    setIsSpeaking(false);
    setCallDuration(0);
    console.log('Conversation ended');
  }, [stopRecording]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (isConnected) {
        endConversation();
      }
    };
  }, [isConnected, endConversation]);

  return {
    isConnected,
    transcript,
    isListening,
    isSpeaking,
    error,
    callDuration,
    startConversation,
    endConversation,
  };
};
