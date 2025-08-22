import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import type { FileUploadStatus, HealthStatus } from '../lib/api';

// Types
export interface AppState {
  // UI State
  sidebarOpen: boolean;
  theme: 'light' | 'dark';
  loading: boolean;
  
  // System State
  healthStatus: HealthStatus | null;
  lastHealthCheck: Date | null;
  
  // WebSocket State
  wsConnected: boolean;
  wsReconnecting: boolean;
  lastWebSocketMessage: any;
  
  // Notifications
  notifications: Notification[];
  
  // Actions
  setSidebarOpen: (open: boolean) => void;
  setTheme: (theme: 'light' | 'dark') => void;
  setLoading: (loading: boolean) => void;
  setHealthStatus: (status: HealthStatus) => void;
  setWsConnected: (connected: boolean) => void;
  setWsReconnecting: (reconnecting: boolean) => void;
  setWebSocketMessage: (message: any) => void;
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp'>) => void;
  removeNotification: (id: string) => void;
  clearNotifications: () => void;
}

export interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message?: string;
  timestamp: Date;
  persistent?: boolean;
}

// Create the store
export const useAppStore = create<AppState>((set, get) => ({
  // Initial state
  sidebarOpen: true,
  theme: 'light',
  loading: false,
  healthStatus: null,
  lastHealthCheck: null,
  wsConnected: false,
  wsReconnecting: false,
  lastWebSocketMessage: null,
  notifications: [],
  
  // Actions
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  
  setTheme: (theme) => {
    set({ theme });
    document.documentElement.classList.toggle('dark', theme === 'dark');
  },
  
  setLoading: (loading) => set({ loading }),
  
  setHealthStatus: (status) => set({ 
    healthStatus: status, 
    lastHealthCheck: new Date() 
  }),
  
  setWsConnected: (connected) => set({ wsConnected: connected }),
  
  setWsReconnecting: (reconnecting) => set({ wsReconnecting: reconnecting }),
  
  setWebSocketMessage: (message) => set({ lastWebSocketMessage: message }),
  
  addNotification: (notification) => {
    const newNotification: Notification = {
      ...notification,
      id: Math.random().toString(36).substr(2, 9),
      timestamp: new Date(),
    };
    
    set((state) => ({
      notifications: [...state.notifications, newNotification]
    }));
    
    // Auto-remove non-persistent notifications after 5 seconds
    if (!newNotification.persistent) {
      setTimeout(() => {
        get().removeNotification(newNotification.id);
      }, 5000);
    }
  },
  
  removeNotification: (id) => set((state) => ({
    notifications: state.notifications.filter(n => n.id !== id)
  })),
  
  clearNotifications: () => set({ notifications: [] }),
}));

// Selectors - commented out temporarily to debug hooks issue
// export const useTheme = () => useAppStore((state) => state.theme);
// export const useSidebarOpen = () => useAppStore((state) => state.sidebarOpen);
// export const useLoading = () => useAppStore((state) => state.loading);
// export const useHealthStatus = () => useAppStore((state) => state.healthStatus);
// export const useWsStatus = () => useAppStore((state) => ({ 
//   connected: state.wsConnected, 
//   reconnecting: state.wsReconnecting 
// }));
// export const useNotifications = () => useAppStore((state) => state.notifications);