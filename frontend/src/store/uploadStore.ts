import { create } from 'zustand';
import type { UploadTask } from '@/types/print';

interface UploadState {
  uploads: UploadTask[];
  addUpload: (task: UploadTask) => void;
  updateProgress: (fileId: string, progress: number, uploadedChunks: number) => void;
  setTaskStatus: (fileId: string, status: UploadTask['status'], error?: string) => void;
  setFileId: (tempId: string, fileId: string, uploadId: string) => void;
  removeUpload: (fileId: string) => void;
  clearCompleted: () => void;
}

export const useUploadStore = create<UploadState>((set) => ({
  uploads: [],

  addUpload: (task) =>
    set((state) => ({ uploads: [...state.uploads, task] })),

  updateProgress: (fileId, progress, uploadedChunks) =>
    set((state) => ({
      uploads: state.uploads.map((u) =>
        u.fileId === fileId || (u as any)._tempId === fileId
          ? { ...u, progress, uploadedChunks }
          : u
      ),
    })),

  setTaskStatus: (fileId, status, error) =>
    set((state) => ({
      uploads: state.uploads.map((u) =>
        u.fileId === fileId || (u as any)._tempId === fileId
          ? { ...u, status, error }
          : u
      ),
    })),

  setFileId: (tempId, fileId, uploadId) =>
    set((state) => ({
      uploads: state.uploads.map((u) =>
        (u as any)._tempId === tempId
          ? { ...u, fileId, uploadId, _tempId: undefined }
          : u
      ),
    })),

  removeUpload: (fileId) =>
    set((state) => ({
      uploads: state.uploads.filter((u) => u.fileId !== fileId),
    })),

  clearCompleted: () =>
    set((state) => ({
      uploads: state.uploads.filter((u) => u.status !== 'completed' && u.status !== 'failed'),
    })),
}));
