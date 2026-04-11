'use client';

import { useState, useEffect } from 'react';
import { getBackendUrl, setBackendUrl as saveBackendUrl, resetBackendUrl, checkBackendConnection } from '@/lib/api-unified';

interface SettingsPanelProps {
  onClose?: () => void;
}

export default function SettingsPanel({ onClose }: SettingsPanelProps) {
  const [backendUrl, setBackendUrl] = useState('');
  const [connectionStatus, setConnectionStatus] = useState<'unknown' | 'connected' | 'error'>('unknown');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    // Load saved backend URL from unified client
    const savedUrl = getBackendUrl();
    setBackendUrl(savedUrl);
    checkConnection(savedUrl);
  }, []);

  const checkConnection = async (url: string) => {
    setIsLoading(true);
    try {
      // Remove trailing slash for consistency
      const cleanUrl = url.replace(/\/$/, '');

      // Test connection using unified client
      const connected = await checkBackendConnection();

      if (connected) {
        setConnectionStatus('connected');
        // Save using unified client
        saveBackendUrl(cleanUrl);
      } else {
        setConnectionStatus('error');
      }
    } catch (error) {
      setConnectionStatus('error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = () => {
    if (backendUrl.trim()) {
      checkConnection(backendUrl.trim());
    }
  };

  const handleReset = () => {
    const defaultUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    setBackendUrl(defaultUrl);
    resetBackendUrl();
    setConnectionStatus('unknown');
  };

  const getStatusColor = () => {
    switch (connectionStatus) {
      case 'connected': return 'text-green-600';
      case 'error': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getStatusText = () => {
    switch (connectionStatus) {
      case 'connected': return '✓ Connected';
      case 'error': return '✗ Connection Failed';
      default: return '○ Unknown';
    }
  };

  const commonBackendUrls = [
    { label: 'Local (default)', url: 'http://localhost:8000' },
    { label: 'Local (alternative)', url: 'http://127.0.0.1:8000' },
    { label: 'Network (local IP)', url: 'http://192.168.1.100:8000' },
    { label: 'Production', url: process.env.NEXT_PUBLIC_API_URL || '' },
  ];

  return (
    <div className="p-6 bg-white rounded-lg shadow-lg">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold">Settings</h2>
        {onClose && (
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
          >
            ✕
          </button>
        )}
      </div>

      <div className="space-y-4">
        {/* Backend URL Configuration */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Backend API URL
          </label>
          <div className="flex gap-2">
            <input
              type="url"
              value={backendUrl}
              onChange={(e) => setBackendUrl(e.target.value)}
              placeholder="http://localhost:8000"
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              onClick={handleSave}
              disabled={isLoading}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {isLoading ? 'Testing...' : 'Test & Save'}
            </button>
            <button
              onClick={handleReset}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300"
            >
              Reset
            </button>
          </div>

          {/* Connection Status */}
          <div className={`mt-2 text-sm ${getStatusColor()}`}>
            Status: {getStatusText()}
          </div>
        </div>

        {/* Quick Select Common URLs */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Quick Select
          </label>
          <div className="grid grid-cols-2 gap-2">
            {commonBackendUrls.map((option) => (
              <button
                key={option.label}
                onClick={() => setBackendUrl(option.url)}
                className="px-3 py-2 text-sm border border-gray-300 rounded-md hover:bg-gray-50 text-left"
              >
                <div className="font-medium">{option.label}</div>
                <div className="text-xs text-gray-500 truncate">{option.url}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Instructions */}
        <div className="mt-4 p-4 bg-blue-50 rounded-md">
          <h3 className="font-medium text-blue-900 mb-2">📝 Local Backend Setup</h3>
          <ol className="text-sm text-blue-800 space-y-1 list-decimal list-inside">
            <li>Run your backend: <code className="bg-blue-100 px-1 rounded">python -m uvicorn src.api.main:create_app --factory --reload</code></li>
            <li>Make sure CORS allows your Vercel domain</li>
            <li>Enter your local URL above (usually http://localhost:8000)</li>
            <li>Click &quot;Test & Save&quot; to verify connection</li>
          </ol>
        </div>

        {/* Current Configuration Info */}
        <div className="mt-4 p-4 bg-gray-50 rounded-md">
          <h3 className="font-medium text-gray-900 mb-2">ℹ️ Configuration Info</h3>
          <div className="text-sm text-gray-700 space-y-1">
            <div><strong>Current Backend:</strong> {backendUrl || 'Not configured'}</div>
            <div><strong>Environment:</strong> {process.env.NODE_ENV}</div>
            <div><strong>Default URL:</strong> {process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}</div>
          </div>
        </div>
      </div>
    </div>
  );
}
