/**
 * ConversationInterface - Main conversation UI component
 * Displays real-time chat, controls, and status indicators
 */

import React, { useEffect, useRef } from 'react';
import { Mic, Phone } from 'lucide-react';
import { useConversation } from '../hooks/useConversation';

const formatTime = (seconds) => {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
};

export const ConversationInterface = ({ agentId, agentName }) => {
  const {
    isConnected,
    transcript,
    isListening,
    isSpeaking,
    error,
    callDuration,
    startConversation,
    endConversation,
  } = useConversation(agentId);

  const transcriptEndRef = useRef(null);

  // Auto-scroll to latest message
  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [transcript]);

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow-lg">
        <div className="max-w-4xl mx-auto px-4 py-6 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold">{agentName || 'AI Agent'}</h1>
            <p className="text-blue-100 text-sm">Ready to assist you</p>
          </div>
          <div className="text-right">
            <div className="text-3xl font-mono font-bold">{formatTime(callDuration)}</div>
            <div className="text-blue-100 text-sm">Call duration</div>
          </div>
        </div>
      </header>

      {/* Error Banner */}
      {error && (
        <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-4 mx-4 mt-4 rounded">
          <p className="font-bold">Error</p>
          <p className="text-sm">{error}</p>
        </div>
      )}

      {/* Transcript Panel */}
      <div className="flex-1 overflow-y-auto p-4 max-w-4xl mx-auto w-full">
        <div className="space-y-4">
          {transcript.length === 0 && !isConnected && (
            <div className="text-center py-12 text-gray-500">
              <p>Click the button below to start a conversation</p>
            </div>
          )}

          {transcript.length === 0 && isConnected && (
            <div className="text-center py-12 text-gray-500">
              <div className="flex justify-center mb-4">
                <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
              </div>
              <p>Listening... Start speaking</p>
            </div>
          )}

          {transcript.map((msg, idx) => (
            <div
              key={idx}
              className={`flex ${msg.speaker === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                  msg.speaker === 'user'
                    ? 'bg-blue-500 text-white rounded-br-none'
                    : 'bg-gray-300 text-gray-900 rounded-bl-none'
                }`}
              >
                <p className="text-sm font-semibold mb-1">
                  {msg.speaker === 'user' ? 'You' : agentName || 'Agent'}
                </p>
                <p className="break-words">{msg.text}</p>
                <p className="text-xs mt-1 opacity-70">
                  {new Date(msg.timestamp).toLocaleTimeString()}
                </p>
              </div>
            </div>
          ))}

          {/* Status Indicators */}
          {isListening && (
            <div className="flex justify-center">
              <div className="bg-blue-100 text-blue-700 px-4 py-2 rounded-full text-sm flex items-center gap-2">
                <div className="w-2 h-2 bg-blue-700 rounded-full animate-pulse"></div>
                Listening...
              </div>
            </div>
          )}

          {isSpeaking && (
            <div className="flex justify-center">
              <div className="bg-green-100 text-green-700 px-4 py-2 rounded-full text-sm flex items-center gap-2">
                <div className="w-2 h-2 bg-green-700 rounded-full animate-pulse"></div>
                Agent speaking...
              </div>
            </div>
          )}

          <div ref={transcriptEndRef} />
        </div>
      </div>

      {/* Controls */}
      <div className="bg-white border-t border-gray-200 p-4 shadow-lg">
        <div className="max-w-4xl mx-auto flex justify-center gap-4">
          {!isConnected ? (
            <button
              onClick={startConversation}
              className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={isConnected}
            >
              <Mic size={20} />
              Start Conversation
            </button>
          ) : (
            <>
              <button
                onClick={endConversation}
                className="flex items-center gap-2 px-6 py-3 bg-red-600 text-white rounded-lg font-semibold hover:bg-red-700 transition"
              >
                <Phone size={20} />
                End Call
              </button>
              {isListening && (
                <div className="flex items-center gap-2 px-4 py-3 bg-gray-100 rounded-lg text-gray-700">
                  <Mic size={20} className="animate-pulse" />
                  Microphone active
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Mobile responsive adjustments */}
      <style jsx>{`
        @media (max-width: 640px) {
          header h1 {
            font-size: 1.5rem;
          }
          .max-w-xs {
            max-width: 85vw;
          }
        }
      `}</style>
    </div>
  );
};

export default ConversationInterface;
