import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import type { ChatResponse, QueryClassification } from '../lib/api';

// Types
export interface ChatMessage {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  queryType?: string;
  analysisType?: string | null;
  isStreaming?: boolean;
  error?: string;
}

export interface ChatSession {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: Date;
  updatedAt: Date;
}

export interface ChatState {
  // Current session
  currentSession: ChatSession | null;
  
  // All sessions
  sessions: ChatSession[];
  
  // UI state
  isLoading: boolean;
  isStreaming: boolean;
  
  // Query suggestions
  querySuggestions: string[];
  
  // Current query classification
  currentClassification: QueryClassification | null;
  
  // Actions
  createSession: (title?: string) => string;
  setCurrentSession: (sessionId: string) => void;
  deleteSession: (sessionId: string) => void;
  updateSessionTitle: (sessionId: string, title: string) => void;
  
  addMessage: (sessionId: string, message: Omit<ChatMessage, 'id' | 'timestamp'>) => string;
  updateMessage: (sessionId: string, messageId: string, update: Partial<ChatMessage>) => void;
  deleteMessage: (sessionId: string, messageId: string) => void;
  
  setLoading: (loading: boolean) => void;
  setStreaming: (streaming: boolean) => void;
  setQuerySuggestions: (suggestions: string[]) => void;
  setCurrentClassification: (classification: QueryClassification | null) => void;
  
  clearCurrentSession: () => void;
  clearAllSessions: () => void;
}

// Helper functions
const generateId = () => `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

const generateSessionTitle = (firstMessage?: string) => {
  if (!firstMessage) return 'New Chat';
  
  // Extract first few words for title
  const words = firstMessage.trim().split(' ').slice(0, 6);
  let title = words.join(' ');
  
  if (firstMessage.length > title.length) {
    title += '...';
  }
  
  return title || 'New Chat';
};

// Create the store
export const useChatStore = create<ChatState>((set, get) => ({
  // Initial state
  currentSession: null,
  sessions: [],
  isLoading: false,
  isStreaming: false,
  querySuggestions: [],
  currentClassification: null,
  
  // Actions
  createSession: (title) => {
    const sessionId = generateId();
    const now = new Date();
    
    const newSession: ChatSession = {
      id: sessionId,
      title: title || 'New Chat',
      messages: [],
      createdAt: now,
      updatedAt: now,
    };
    
    set((state) => ({
      sessions: [newSession, ...state.sessions],
      currentSession: newSession,
    }));
    
    return sessionId;
  },
  
  setCurrentSession: (sessionId) => {
    const session = get().sessions.find(s => s.id === sessionId);
    if (session) {
      set({ currentSession: session });
    }
  },
  
  deleteSession: (sessionId) => {
    set((state) => {
      const newSessions = state.sessions.filter(s => s.id !== sessionId);
      const newCurrentSession = state.currentSession?.id === sessionId 
        ? (newSessions[0] || null) 
        : state.currentSession;
      
      return {
        sessions: newSessions,
        currentSession: newCurrentSession,
      };
    });
  },
  
  updateSessionTitle: (sessionId, title) => {
    set((state) => {
      const updatedSessions = state.sessions.map(session => 
        session.id === sessionId 
          ? { ...session, title, updatedAt: new Date() }
          : session
      );
      
      const updatedCurrentSession = state.currentSession?.id === sessionId
        ? { ...state.currentSession, title, updatedAt: new Date() }
        : state.currentSession;
      
      return {
        sessions: updatedSessions,
        currentSession: updatedCurrentSession,
      };
    });
  },
  
  addMessage: (sessionId, message) => {
    const messageId = generateId();
    const now = new Date();
    
    const newMessage: ChatMessage = {
      ...message,
      id: messageId,
      timestamp: now,
    };
    
    set((state) => {
      const updatedSessions = state.sessions.map(session => {
        if (session.id === sessionId) {
          const updatedSession = {
            ...session,
            messages: [...session.messages, newMessage],
            updatedAt: now,
          };
          
          // Auto-generate title from first user message
          if (session.messages.length === 0 && message.type === 'user' && session.title === 'New Chat') {
            updatedSession.title = generateSessionTitle(message.content);
          }
          
          return updatedSession;
        }
        return session;
      });
      
      const updatedCurrentSession = state.currentSession?.id === sessionId
        ? updatedSessions.find(s => s.id === sessionId) || state.currentSession
        : state.currentSession;
      
      return {
        sessions: updatedSessions,
        currentSession: updatedCurrentSession,
      };
    });
    
    return messageId;
  },
  
  updateMessage: (sessionId, messageId, update) => {
    set((state) => {
      const updatedSessions = state.sessions.map(session => {
        if (session.id === sessionId) {
          return {
            ...session,
            messages: session.messages.map(msg => 
              msg.id === messageId ? { ...msg, ...update } : msg
            ),
            updatedAt: new Date(),
          };
        }
        return session;
      });
      
      const updatedCurrentSession = state.currentSession?.id === sessionId
        ? updatedSessions.find(s => s.id === sessionId) || state.currentSession
        : state.currentSession;
      
      return {
        sessions: updatedSessions,
        currentSession: updatedCurrentSession,
      };
    });
  },
  
  deleteMessage: (sessionId, messageId) => {
    set((state) => {
      const updatedSessions = state.sessions.map(session => {
        if (session.id === sessionId) {
          return {
            ...session,
            messages: session.messages.filter(msg => msg.id !== messageId),
            updatedAt: new Date(),
          };
        }
        return session;
      });
      
      const updatedCurrentSession = state.currentSession?.id === sessionId
        ? updatedSessions.find(s => s.id === sessionId) || state.currentSession
        : state.currentSession;
      
      return {
        sessions: updatedSessions,
        currentSession: updatedCurrentSession,
      };
    });
  },
  
  setLoading: (loading) => set({ isLoading: loading }),
  
  setStreaming: (streaming) => set({ isStreaming: streaming }),
  
  setQuerySuggestions: (suggestions) => set({ querySuggestions: suggestions }),
  
  setCurrentClassification: (classification) => set({ currentClassification: classification }),
  
  clearCurrentSession: () => set({ currentSession: null }),
  
  clearAllSessions: () => set({ 
    sessions: [], 
    currentSession: null 
  }),
}));

// Selectors
export const useCurrentSession = () => useChatStore((state) => state.currentSession);
export const useSessions = () => useChatStore((state) => state.sessions);
export const useChatLoading = () => useChatStore((state) => state.isLoading);
export const useChatStreaming = () => useChatStore((state) => state.isStreaming);
export const useQuerySuggestions = () => useChatStore((state) => state.querySuggestions);
export const useCurrentClassification = () => useChatStore((state) => state.currentClassification);

// Helper selectors
export const useSessionById = (sessionId: string) => 
  useChatStore((state) => state.sessions.find(s => s.id === sessionId));

export const useMessageById = (sessionId: string, messageId: string) => 
  useChatStore((state) => {
    const session = state.sessions.find(s => s.id === sessionId);
    return session?.messages.find(m => m.id === messageId);
  });

export const useSessionStats = () => 
  useChatStore((state) => {
    const totalSessions = state.sessions.length;
    const totalMessages = state.sessions.reduce((sum, session) => sum + session.messages.length, 0);
    const recentSessions = state.sessions.filter(s => {
      const dayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000);
      return s.updatedAt > dayAgo;
    }).length;
    
    return { totalSessions, totalMessages, recentSessions };
  });