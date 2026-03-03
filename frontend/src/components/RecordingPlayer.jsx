/**
 * RecordingPlayer - Audio recording playback component
 * Displays player controls, progress, and download functionality
 */

import React, { useState, useRef, useEffect } from 'react';
import { Play, Pause, Download, Trash2, Clock, Volume2 } from 'lucide-react';

export const RecordingPlayer = ({ recordingUrl, callId, onDelete }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const audioRef = useRef(null);
  const progressRef = useRef(null);

  // Load audio metadata
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const handleLoadedMetadata = () => {
      setDuration(audio.duration);
      setError(null);
    };

    const handleError = () => {
      setError('Failed to load recording');
      setIsLoading(false);
    };

    const handlePlay = () => {
      setIsPlaying(true);
    };

    const handlePause = () => {
      setIsPlaying(false);
    };

    const handleTimeUpdate = () => {
      setCurrentTime(audio.currentTime);
    };

    const handleEnded = () => {
      setIsPlaying(false);
      setCurrentTime(0);
    };

    audio.addEventListener('loadedmetadata', handleLoadedMetadata);
    audio.addEventListener('error', handleError);
    audio.addEventListener('play', handlePlay);
    audio.addEventListener('pause', handlePause);
    audio.addEventListener('timeupdate', handleTimeUpdate);
    audio.addEventListener('ended', handleEnded);

    return () => {
      audio.removeEventListener('loadedmetadata', handleLoadedMetadata);
      audio.removeEventListener('error', handleError);
      audio.removeEventListener('play', handlePlay);
      audio.removeEventListener('pause', handlePause);
      audio.removeEventListener('timeupdate', handleTimeUpdate);
      audio.removeEventListener('ended', handleEnded);
    };
  }, []);

  const formatTime = (seconds) => {
    if (isNaN(seconds)) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handlePlayPause = () => {
    const audio = audioRef.current;
    if (!audio) return;

    if (isPlaying) {
      audio.pause();
    } else {
      setIsLoading(true);
      audio.play().catch((err) => {
        console.error('Playback error:', err);
        setError('Failed to play recording');
        setIsLoading(false);
      });
      setIsLoading(false);
    }
  };

  const handleProgressClick = (e) => {
    const audio = audioRef.current;
    if (!audio || !progressRef.current) return;

    const rect = progressRef.current.getBoundingClientRect();
    const percent = (e.clientX - rect.left) / rect.width;
    const newTime = percent * duration;
    audio.currentTime = Math.max(0, Math.min(newTime, duration));
  };

  const handleVolumeChange = (e) => {
    const audio = audioRef.current;
    const newVolume = parseFloat(e.target.value);
    setVolume(newVolume);
    if (audio) {
      audio.volume = newVolume;
    }
  };

  const handleDownload = async () => {
    try {
      setIsLoading(true);
      const response = await fetch(recordingUrl);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `call-${callId}.mp3`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('Download error:', err);
      setError('Failed to download recording');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm('Are you sure you want to delete this recording?')) {
      return;
    }

    try {
      setIsLoading(true);
      const response = await fetch(`/api/v1/calls/${callId}/recording`, {
        method: 'DELETE',
      });

      if (response.ok) {
        onDelete?.(callId);
      } else {
        setError('Failed to delete recording');
      }
    } catch (err) {
      console.error('Delete error:', err);
      setError('Failed to delete recording');
    } finally {
      setIsLoading(false);
    }
  };

  if (!recordingUrl) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-yellow-700">
        <p>No recording available for this call</p>
      </div>
    );
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded mb-4 p-3">
          {error}
        </div>
      )}

      {/* Audio element */}
      <audio
        ref={audioRef}
        src={recordingUrl}
        crossOrigin="anonymous"
      />

      {/* Player controls */}
      <div className="space-y-4">
        {/* Play/Pause and Progress */}
        <div className="flex items-center gap-4">
          {/* Play/Pause button */}
          <button
            onClick={handlePlayPause}
            disabled={isLoading}
            className="flex-shrink-0 p-2 rounded-full bg-blue-100 text-blue-600 hover:bg-blue-200 disabled:opacity-50 disabled:cursor-not-allowed transition"
          >
            {isPlaying ? <Pause size={20} /> : <Play size={20} />}
          </button>

          {/* Progress bar */}
          <div className="flex-1">
            <div
              ref={progressRef}
              onClick={handleProgressClick}
              className="relative h-2 bg-gray-200 rounded cursor-pointer hover:h-3 transition-all"
            >
              <div
                className="h-full bg-blue-600 rounded"
                style={{
                  width: `${duration ? (currentTime / duration) * 100 : 0}%`,
                }}
              />
            </div>
          </div>

          {/* Time display */}
          <div className="flex-shrink-0 text-sm text-gray-600 min-w-20 text-right">
            {formatTime(currentTime)} / {formatTime(duration)}
          </div>
        </div>

        {/* Volume and Download/Delete */}
        <div className="flex items-center justify-between">
          {/* Volume control */}
          <div className="flex items-center gap-2">
            <Volume2 size={16} className="text-gray-400" />
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={volume}
              onChange={handleVolumeChange}
              className="w-24"
            />
          </div>

          {/* Download and Delete buttons */}
          <div className="flex items-center gap-2">
            <button
              onClick={handleDownload}
              disabled={isLoading}
              className="flex items-center gap-2 px-3 py-1 text-sm rounded bg-blue-50 text-blue-600 hover:bg-blue-100 disabled:opacity-50 disabled:cursor-not-allowed transition"
            >
              <Download size={16} />
              Download
            </button>

            <button
              onClick={handleDelete}
              disabled={isLoading}
              className="flex items-center gap-2 px-3 py-1 text-sm rounded bg-red-50 text-red-600 hover:bg-red-100 disabled:opacity-50 disabled:cursor-not-allowed transition"
            >
              <Trash2 size={16} />
              Delete
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RecordingPlayer;
