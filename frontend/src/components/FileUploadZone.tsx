import React from 'react';
import { Upload, message } from 'antd';
import { InboxOutlined } from '@ant-design/icons';
import type { UploadProps } from 'antd';

const { Dragger } = Upload;

interface FileUploadZoneProps {
  onFilesSelected: (files: File[]) => void;
  maxSize?: number;
  accept?: string;
}

const DEFAULT_MAX_SIZE = 100 * 1024 * 1024; // 100MB

const FileUploadZone: React.FC<FileUploadZoneProps> = ({
  onFilesSelected,
  maxSize = DEFAULT_MAX_SIZE,
  accept,
}) => {
  const beforeUpload: UploadProps['beforeUpload'] = (file, fileList) => {
    if (file.size > maxSize) {
      const sizeMB = (maxSize / (1024 * 1024)).toFixed(0);
      message.warning(`文件 "${file.name}" 超过 ${sizeMB}MB 大小限制`);
      return Upload.LIST_IGNORE;
    }

    if (fileList.every((f) => f.uid !== file.uid || f === file)) {
      const files = fileList.map((f) => f as unknown as File);
      onFilesSelected(files);
    }

    return false;
  };

  const customRequest: UploadProps['customRequest'] = ({ onSuccess }) => {
    if (onSuccess) {
      onSuccess('ok');
    }
  };

  return (
    <Dragger
      multiple
      accept={accept}
      beforeUpload={beforeUpload}
      customRequest={customRequest}
      showUploadList={false}
    >
      <p className="ant-upload-drag-icon">
        <InboxOutlined />
      </p>
      <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
      <p className="ant-upload-hint">
        支持单个或批量上传，单个文件最大 {(maxSize / (1024 * 1024)).toFixed(0)}MB
      </p>
    </Dragger>
  );
};

export default FileUploadZone;
