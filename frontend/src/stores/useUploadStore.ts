import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import type { FileUploadStatus } from '../lib/api';

// Types
export interface UploadProgress {
  fileId: string;
  filename: string;
  progress: number;
  status: 'uploading' | 'processing' | 'completed' | 'failed';
  error?: string;
}

export interface UploadState {
  // Upload state
  uploads: Map<string, UploadProgress>;
  uploadHistory: FileUploadStatus[];
  isUploading: boolean;
  
  // Drag and drop state
  isDragOver: boolean;
  
  // Actions
  startUpload: (upload: { id: string; name: string; size: number; type: string; status: string; progress: number; uploadedAt: Date }) => void;
  updateUploadProgress: (fileId: string, progress: number) => void;
  updateUploadStatus: (fileId: string, status: UploadProgress['status'], error?: string) => void;
  updateUpload: (fileId: string, update: Partial<UploadProgress>) => void;
  completeUpload: (fileId: string, update: Partial<UploadProgress>) => void;
  removeUpload: (fileId: string) => void;
  setUploadHistory: (history: FileUploadStatus[]) => void;
  updateUploadHistoryItem: (fileId: string, update: Partial<FileUploadStatus>) => void;
  setDragOver: (isDragOver: boolean) => void;
  clearUploads: () => void;
  getUploadStats: () => { total: number; completed: number; failed: number; processing: number };
  headerMapping?: Record<string, string>;
}

// Create the store
export const useUploadStore = create<UploadState>(devtools((set, get) => ({
  // Initial state
  uploads: new Map(),
  uploadHistory: [],
  isUploading: false,
  isDragOver: false,
  
  // Actions
  startUpload: (upload) => {
    set((state) => {
      const newUploads = new Map(state.uploads);
      newUploads.set(upload.id, {
        fileId: upload.id,
        filename: upload.name,
        progress: upload.progress || 0,
        status: upload.status,
      });
      
      return {
        uploads: newUploads,
        isUploading: true,
      };
    });
  },
  
  updateUploadProgress: (fileId, progress) => {
    set((state) => {
      const newUploads = new Map(state.uploads);
      const upload = newUploads.get(fileId);
      
      if (upload) {
        newUploads.set(fileId, {
          ...upload,
          progress,
        });
      }
      
      return { uploads: newUploads };
    });
  },
  
  updateUploadStatus: (fileId, status, error) => {
    set((state) => {
      const newUploads = new Map(state.uploads);
      const upload = newUploads.get(fileId);
      
      if (upload) {
        newUploads.set(fileId, {
          ...upload,
          status,
          error,
        });
      }
      
      // Check if any uploads are still in progress
      const hasActiveUploads = Array.from(newUploads.values())
        .some(u => u.status === 'uploading' || u.status === 'processing');
      
      return {
        uploads: newUploads,
        isUploading: hasActiveUploads,
      };
    });
  },
  
  updateUpload: (fileId, update) => {
    set((state) => {
      const newUploads = new Map(state.uploads);
      const upload = newUploads.get(fileId);
      
      if (upload) {
        newUploads.set(fileId, {
          ...upload,
          ...update
        });
      }
      
      // Check if any uploads are still in progress
      const hasActiveUploads = Array.from(newUploads.values())
        .some(u => u.status === 'uploading' || u.status === 'processing');
      
      return {
        uploads: newUploads,
        isUploading: hasActiveUploads,
      };
    });
  },
  
  completeUpload: (fileId, update) => {
    set((state) => {
      const newUploads = new Map(state.uploads);
      const upload = newUploads.get(fileId);
      
      if (upload) {
        newUploads.set(fileId, {
          ...upload,
          ...update
        });
      }
      
      // Check if any uploads are still in progress
      const hasActiveUploads = Array.from(newUploads.values())
        .some(u => u.status === 'uploading' || u.status === 'processing');
      
      return {
        uploads: newUploads,
        isUploading: hasActiveUploads,
      };
    });
  },
  
  removeUpload: (fileId) => {
    set((state) => {
      const newUploads = new Map(state.uploads);
      newUploads.delete(fileId);
      
      const hasActiveUploads = Array.from(newUploads.values())
        .some(u => u.status === 'uploading' || u.status === 'processing');
      
      return {
        uploads: newUploads,
        isUploading: hasActiveUploads,
      };
    });
  },
  
  setUploadHistory: (history) => {
    set({ uploadHistory: history });
  },
  
  updateUploadHistoryItem: (fileId, update) => {
    set((state) => ({
      uploadHistory: state.uploadHistory.map(item => 
        item.file_id === fileId ? { ...item, ...update } : item
      )
    }));
  },
  
  setDragOver: (isDragOver) => {
    set({ isDragOver });
  },
  
  clearUploads: () => {
    set({
      uploads: new Map(),
      isUploading: false,
    });
  },
  
  // Stats calculation
  getUploadStats: () => {
    const uploads = Array.from(get().uploads.values());
    const total = uploads.length;
    const completed = uploads.filter(u => u.status === 'completed').length;
    const failed = uploads.filter(u => u.status === 'failed').length;
    const processing = uploads.filter(u => u.status === 'processing').length;
    
    return { total, completed, failed, processing };
  },
})));

// Selectors
export const useUploads = () => useUploadStore((state) => Array.from(state.uploads.values()));
export const useUploadHistory = () => useUploadStore((state) => state.uploadHistory);
export const useIsUploading = () => useUploadStore((state) => state.isUploading);
export const useIsDragOver = () => useUploadStore((state) => state.isDragOver);
export const useUploadById = (fileId: string) => useUploadStore((state) => state.uploads.get(fileId));

// Helper functions
export const getUploadStats = (uploads: UploadProgress[]) => {
  const total = uploads.length;
  const completed = uploads.filter(u => u.status === 'completed').length;
  const failed = uploads.filter(u => u.status === 'failed').length;
  const inProgress = uploads.filter(u => u.status === 'uploading' || u.status === 'processing').length;
  
  return { total, completed, failed, inProgress };
};

export const getOverallProgress = (uploads: UploadProgress[]) => {
  if (uploads.length === 0) return 0;
  
  const totalProgress = uploads.reduce((sum, upload) => {
    if (upload.status === 'completed') return sum + 100;
    if (upload.status === 'failed') return sum + 0;
    return sum + upload.progress;
  }, 0);
  
  return Math.round(totalProgress / uploads.length);
};