import axios, { type AxiosInstance, type AxiosResponse } from 'axios';
import toast from 'react-hot-toast';

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000';

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  (error) => {
    // Handle common errors
    if (error.response?.status === 401) {
      // Unauthorized - redirect to login or clear auth
      localStorage.removeItem('auth_token');
      toast.error('Session expired. Please log in again.');
    } else if (error.response?.status === 500) {
      toast.error('Server error. Please try again later.');
    } else if (error.code === 'NETWORK_ERROR') {
      toast.error('Network error. Please check your connection.');
    }
    
    return Promise.reject(error);
  }
);

// Types
export interface FileUploadResponse {
  file_id: string;
  filename: string;
  status: string;
  message: string;
}

export interface FileUploadStatus {
  file_id: string;
  filename: string;
  status: 'uploaded' | 'processing' | 'completed' | 'failed';
  progress_percentage: number;
  records_processed?: number;
  error_details?: any;
  processing_summary?: any;
  created_at: string;
  processing_started_at?: string;
  processing_completed_at?: string;
  headerMapping?: Record<string, string>; // Mapping of target fields to source fields
}

export interface ChatRequest {
  query: string;
  session_id?: string;
  response_format?: string;
  auto_classify?: string; // "true" or "false" as string
  student_id?: string;
  course_id?: string;
}

export interface ChatResponse {
  session_id: string;
  query: string;
  response: string | object; // Can be string or parsed JSON object for structured responses
  classification: string;
  analysis_type?: string | null;
}

export interface QueryClassification {
  query_type: string;
  confidence: number;
  suggested_format: string;
  parameters: Record<string, any>;
}

export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'error';
  timestamp: string;
  services: {
    database: string;
    vector_store: string;
    llm_services: string;
  };
}

// API Functions

// Health Check
export const healthCheck = async (): Promise<HealthStatus> => {
  const response = await api.get('/health');
  return response.data;
};

// File Upload APIs
export const uploadFile = async (
  file: File, 
  fileType: 'survey' | 'demographics' = 'survey',
  onProgress?: (progress: number) => void
): Promise<FileUploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('file_type', fileType);
  
  const response = await api.post('/api/upload/file', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (progressEvent.total && onProgress) {
        const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(progress);
      }
    },
  });
  
  return response.data;
};

export const uploadMultipleFiles = async (
  files: File[], 
  fileTypes: ('survey' | 'demographics')[] = ['survey', 'demographics'],
  onProgress?: (progress: number) => void
): Promise<FileUploadResponse[]> => {
  const formData = new FormData();
  
  // Append all files
  files.forEach(file => {
    formData.append('files', file);
  });
  
  // Append file types as comma-separated string
  formData.append('file_types', fileTypes.join(','));
  
  const response = await api.post('/api/upload/files', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (progressEvent.total && onProgress) {
        const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(progress);
      }
    },
  });
  
  return response.data;
};

export const uploadBothFiles = async (
  npsFile: File,
  demographicsFile: File,
  onProgress?: (progress: number) => void
): Promise<FileUploadResponse[]> => {
  const formData = new FormData();
  
  // Append files with specific field names
  formData.append('nps_file', npsFile);
  formData.append('demographics_file', demographicsFile);
  
  const response = await api.post('/api/upload/both-files', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (progressEvent.total && onProgress) {
        const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(progress);
      }
    },
  });
  
  return response.data;
};

export const getUploadStatus = async (fileId: string): Promise<FileUploadStatus> => {
  const response = await api.get(`/api/upload/status/${fileId}`);
  return response.data;
};

export const getUploadHistory = async (): Promise<FileUploadStatus[]> => {
  const response = await api.get('/api/upload/history');
  return response.data;
};

export const deleteUpload = async (fileId: string): Promise<{ message: string }> => {
  const response = await api.delete(`/api/upload/file/${fileId}`);
  return response.data;
};

export const validateFile = async (file: File): Promise<{ valid: boolean; issues?: string[]; suggestions?: string[] }> => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await api.post('/api/upload/validate', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  
  return response.data;
};

export const getFilePreview = async (fileId: string): Promise<{ headers: string[], rows: any[] }> => {
  const response = await api.get(`/api/upload/preview/${fileId}`);
  return response.data;
};

// Chat APIs
export const sendChatMessage = async (request: ChatRequest): Promise<ChatResponse> => {
  const response = await api.post('/api/chat/query', request);
  return response.data;
};

export const classifyQuery = async (message: string): Promise<QueryClassification> => {
  const response = await api.get('/api/chat/classify', {
    params: { query: message }
  });
  return response.data;
};

export const getQuerySuggestions = async (): Promise<string[]> => {
  try {
    const response = await api.get('/api/chat/suggestions');
    return response.data.suggestions || [];
  } catch (error) {
    console.error('Error fetching query suggestions:', error);
    return [];
  }
};

// WebSocket Connection
export class WebSocketManager {
  private ws: WebSocket | null = null;
  private clientId: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private eventHandlers: Map<string, (data: any) => void> = new Map();
  private subscriptions: Set<string> = new Set();

  constructor(clientId?: string) {
    this.clientId = clientId || this.generateClientId();
  }

  private generateClientId(): string {
    return `client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        const wsUrl = `${WS_BASE_URL}/api/ws/connect/${this.clientId}`;
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.reconnectAttempts = 0;
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };

        this.ws.onclose = (event) => {
          console.log('WebSocket disconnected:', event.code, event.reason);
          this.attemptReconnect();
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          // Don't reject the promise, just log the error
          // This prevents the error from bubbling up and breaking the UI
          console.warn('WebSocket connection failed, but continuing without real-time updates');
          resolve(); // Resolve anyway to prevent UI from breaking
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  private handleMessage(data: any) {
    const { type } = data;
    
    // Call specific event handler if registered
    const handler = this.eventHandlers.get(type);
    if (handler) {
      handler(data);
    }
    
    // Call general event handler
    const generalHandler = this.eventHandlers.get('*');
    if (generalHandler) {
      generalHandler(data);
    }
  }

  private attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
      
      console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`);
      
      setTimeout(() => {
        this.connect().catch((error) => {
          console.error('Reconnection failed:', error);
        });
      }, delay);
    } else {
      console.error('Max reconnection attempts reached');
      toast.error('Connection lost. Please refresh the page.');
    }
  }

  subscribe(subscriptionType: string) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'subscribe',
        subscription_type: subscriptionType
      }));
      this.subscriptions.add(subscriptionType);
    }
  }

  unsubscribe(subscriptionType: string) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'unsubscribe',
        subscription_type: subscriptionType
      }));
      this.subscriptions.delete(subscriptionType);
    }
  }

  on(eventType: string, handler: (data: any) => void) {
    this.eventHandlers.set(eventType, handler);
  }

  off(eventType: string) {
    this.eventHandlers.delete(eventType);
  }

  send(message: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected');
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.eventHandlers.clear();
    this.subscriptions.clear();
  }

  getConnectionState(): number {
    return this.ws ? this.ws.readyState : WebSocket.CLOSED;
  }

  isConnected(): boolean {
    return this.ws ? this.ws.readyState === WebSocket.OPEN : false;
  }
}

// Export singleton WebSocket manager
export const wsManager = new WebSocketManager();

// Utility functions
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

export const isValidFileType = (file: File): boolean => {
  const allowedTypes = [
    'text/csv',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
  ];
  
  return allowedTypes.includes(file.type) || 
         file.name.toLowerCase().endsWith('.csv') ||
         file.name.toLowerCase().endsWith('.xlsx') ||
         file.name.toLowerCase().endsWith('.xls');
};

export { api };
export default api;

// Re-export to ensure proper module resolution
export type { FileUploadStatus };