import { useEffect } from 'react';
import { RouterProvider } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { router } from './lib/router';
import { useAppStore } from './stores/useAppStore';
import { wsManager } from './lib/api';
import './App.css';

function App() {
  const { setWsConnected, setWsReconnecting, addNotification, setTheme, theme } = useAppStore();

  useEffect(() => {
    // Apply theme on app start
    document.documentElement.classList.toggle('dark', theme === 'dark');
  }, [theme]);

  useEffect(() => {
    // Initialize WebSocket connection
    const initializeWebSocket = async () => {
      try {
        setWsReconnecting(true);
        await wsManager.connect();
        setWsConnected(true);
        setWsReconnecting(false);
        
        // Subscribe to general updates
        wsManager.subscribe('upload_progress');
        wsManager.subscribe('analysis_completion');
        wsManager.subscribe('system_status');
        
        // Set up event handlers
        wsManager.on('upload_progress', (data) => {
          // Handle upload progress updates
          console.log('Upload progress:', data);
        });
        
        wsManager.on('analysis_completion', (data) => {
          addNotification({
            type: 'success',
            title: 'Analysis Complete',
            message: `Analysis for ${data.filename} has been completed.`,
          });
        });
        
        wsManager.on('system_status', (data) => {
          if (data.status === 'error') {
            addNotification({
              type: 'error',
              title: 'System Alert',
              message: data.message || 'System experiencing issues',
              persistent: true,
            });
          }
        });
        
        wsManager.on('*', (data) => {
          console.log('WebSocket message:', data);
        });
        
      } catch (error) {
        console.error('Failed to initialize WebSocket:', error);
        setWsConnected(false);
        setWsReconnecting(false);
        
        addNotification({
          type: 'warning',
          title: 'Connection Issue',
          message: 'Real-time updates are not available. Some features may be limited.',
        });
      }
    };

    initializeWebSocket();

    // Cleanup on unmount
    return () => {
      wsManager.disconnect();
    };
  }, [setWsConnected, setWsReconnecting, addNotification]);

  return (
    <>
      <RouterProvider router={router} />
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: theme === 'dark' ? '#374151' : '#ffffff',
            color: theme === 'dark' ? '#f9fafb' : '#111827',
            border: theme === 'dark' ? '1px solid #4b5563' : '1px solid #e5e7eb',
          },
          success: {
            iconTheme: {
              primary: '#10b981',
              secondary: '#ffffff',
            },
          },
          error: {
            iconTheme: {
              primary: '#ef4444',
              secondary: '#ffffff',
            },
          },
        }}
      />
    </>
  );
}

export default App;
