import { useCallback, useRef } from 'react';
import SparkMD5 from 'spark-md5';
import { filesApi } from '@/api/files';
import { useUploadStore } from '@/store/uploadStore';

const CHUNK_SIZE = 5 * 1024 * 1024; // 5MB
const MAX_CONCURRENT = 3;

export function useChunkedUpload() {
  const { addUpload, updateProgress, setTaskStatus, setFileId } = useUploadStore();
  const abortControllers = useRef<Map<string, AbortController>>(new Map());

  const uploadFile = useCallback(async (file: File): Promise<string | null> => {
    const tempId = `${file.name}_${Date.now()}`;

    addUpload({
      file,
      progress: 0,
      status: 'hashing',
      totalChunks: 0,
      uploadedChunks: 0,
      _tempId: tempId,
    } as any);

    try {
      // Calculate MD5
      const buffer = await file.arrayBuffer();
      const md5 = SparkMD5.ArrayBuffer.hash(buffer);

      const totalChunks = Math.ceil(file.size / CHUNK_SIZE);
      setTaskStatus(tempId, 'uploading');

      // Init upload
      const { upload_id, file_id } = await filesApi.initUpload({
        filename: file.name,
        file_size: file.size,
        file_md5: md5,
        total_chunks: totalChunks,
        mime_type: file.type,
      });

      setFileId(tempId, file_id, upload_id);

      // Upload chunks with concurrency control
      const chunks = Array.from({ length: totalChunks }, (_, i) => i);
      let completedChunks = 0;

      const uploadChunk = async (chunkIndex: number): Promise<void> => {
        const start = chunkIndex * CHUNK_SIZE;
        const end = Math.min(start + CHUNK_SIZE, file.size);
        const chunk = file.slice(start, end);

        await filesApi.uploadChunk(upload_id, chunkIndex, chunk);
        completedChunks++;
        const progress = Math.round((completedChunks / totalChunks) * 90); // 90% for upload
        updateProgress(file_id, progress, completedChunks);
      };

      // Process chunks in batches
      for (let i = 0; i < chunks.length; i += MAX_CONCURRENT) {
        const batch = chunks.slice(i, i + MAX_CONCURRENT);
        await Promise.all(batch.map(uploadChunk));
      }

      // Complete upload
      updateProgress(file_id, 95, totalChunks);
      await filesApi.completeUpload({ upload_id, file_id });

      updateProgress(file_id, 100, totalChunks);
      setTaskStatus(file_id, 'completed');

      return file_id;
    } catch (error: any) {
      setTaskStatus(tempId, 'failed', error.message || 'Upload failed');
      return null;
    }
  }, [addUpload, updateProgress, setTaskStatus, setFileId]);

  const cancelUpload = useCallback((fileId: string) => {
    // TODO: implement cancel
  }, []);

  return { uploadFile, cancelUpload };
}
