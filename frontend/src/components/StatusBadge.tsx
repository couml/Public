import React from 'react';
import { Badge } from 'antd';
import type { DeviceStatus } from '@/types/device';

interface StatusBadgeProps {
  status: DeviceStatus;
  size?: 'small' | 'default';
}

const statusMap: Record<DeviceStatus, { color: string; text: string }> = {
  online: { color: '#52c41a', text: '在线' },
  offline: { color: '#8c8c8c', text: '离线' },
  busy: { color: '#fa8c16', text: '繁忙' },
  error: { color: '#ff4d4f', text: '故障' },
};

const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'default' }) => {
  const config = statusMap[status] ?? { color: '#8c8c8c', text: '未知' };
  const fontSize = size === 'small' ? 12 : 14;

  return (
    <Badge
      color={config.color}
      text={<span style={{ fontSize, color: config.color }}>{config.text}</span>}
    />
  );
};

export default StatusBadge;
