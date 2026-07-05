import { useCallback } from 'react';
import { filesApi } from '@/api/files';
import { useUploadStore } from '@/store/uploadStore';

export function useChunkedUpload() {
  const { addUpload, updateProgress, setTaskStatus, removeUpload } = useUploadStore();

  const uploadFile = useCallback(async (file: File): Promise<string | null> => {
    const tempId = `${file.name}_${Date.now()}`;

    addUpload({
      file,
      progress: 0,
      status: 'uploading',
      totalChunks: 1,
      uploadedChunks: 0,
      _tempId: tempId,
    } as any);

    try {
      const result = await filesApi.simpleUpload(file, (pct) => {
        updateProgress(tempId, pct, 1);
      });

      const fileId = result.id;
      updateProgress(tempId, 100, 1);
      setTaskStatus(tempId, 'completed');

      return fileId;
    } catch (error: any) {
      setTaskStatus(tempId, 'failed', error.message || 'Upload failed');
      return null;
    }
  }, [addUpload, updateProgress, setTaskStatus]);

  return { uploadFile };
}
