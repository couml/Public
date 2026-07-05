import React from 'react';
import { List, Progress, Typography, Space } from 'antd';
import { CheckCircleFilled, CloseCircleFilled, LoadingOutlined } from '@ant-design/icons';
import { useUploadStore } from '@/store/uploadStore';
import { formatFileSize } from '@/utils/format';

const { Text } = Typography;

const statusConfig: Record<string, { color: string; icon: React.ReactNode; text: string }> = {
  pending: { color: '#8c8c8c', icon: <LoadingOutlined />, text: '等待中' },
  hashing: { color: '#1677ff', icon: <LoadingOutlined />, text: '计算哈希' },
  uploading: { color: '#1677ff', icon: <LoadingOutlined />, text: '上传中' },
  completed: { color: '#52c41a', icon: <CheckCircleFilled />, text: '已完成' },
  failed: { color: '#ff4d4f', icon: <CloseCircleFilled />, text: '失败' },
};

const UploadProgressList: React.FC = () => {
  const uploads = useUploadStore((s) => s.uploads);

  if (uploads.length === 0) {
    return null;
  }

  return (
    <List
      dataSource={uploads}
      renderItem={(item) => {
        const config = statusConfig[item.status] ?? statusConfig.pending;
        const strokeColor =
          item.status === 'completed' ? '#52c41a' : item.status === 'failed' ? '#ff4d4f' : '#1677ff';
        const percent = Math.round(item.progress);

        return (
          <List.Item style={{ padding: '8px 0' }}>
            <div style={{ width: '100%' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                <Space size={8}>
                  <span style={{ color: config.color }}>{config.icon}</span>
                  <Text ellipsis style={{ maxWidth: 200 }}>
                    {item.file.name}
                  </Text>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    {formatFileSize(item.file.size)}
                  </Text>
                </Space>
                <Text style={{ color: config.color, fontSize: 12, whiteSpace: 'nowrap' }}>
                  {config.text}
                  {item.status === 'failed' && item.error ? `: ${item.error}` : ''}
                </Text>
              </div>
              <Progress
                percent={percent}
                size="small"
                strokeColor={strokeColor}
                status={item.status === 'failed' ? 'exception' : item.status === 'completed' ? 'success' : 'active'}
                showInfo={false}
              />
            </div>
          </List.Item>
        );
      }}
    />
  );
};

export default UploadProgressList;
