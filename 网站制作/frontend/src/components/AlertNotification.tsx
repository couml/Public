import React from 'react';
import { List, Typography, Space, Tag } from 'antd';
import {
  WarningOutlined,
  InfoCircleOutlined,
  CloseCircleOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import type { PrinterAlert } from '@/types/device';

dayjs.extend(relativeTime);

const { Text } = Typography;

const severityConfig: Record<string, { color: string; icon: React.ReactNode; label: string }> = {
  critical: { color: '#ff4d4f', icon: <CloseCircleOutlined />, label: '严重' },
  warning: { color: '#fa8c16', icon: <WarningOutlined />, label: '警告' },
  info: { color: '#1677ff', icon: <InfoCircleOutlined />, label: '信息' },
};

interface AlertNotificationProps {
  alerts: PrinterAlert[];
}

const AlertNotification: React.FC<AlertNotificationProps> = ({ alerts }) => {
  if (alerts.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: 24, color: '#8c8c8c' }}>
        <Text type="secondary">暂无告警</Text>
      </div>
    );
  }

  return (
    <List
      dataSource={alerts}
      renderItem={(alert) => {
        const config = severityConfig[alert.severity] ?? severityConfig.info;
        return (
          <List.Item style={{ padding: '10px 0' }}>
            <List.Item.Meta
              avatar={
                <span style={{ color: config.color, fontSize: 18 }}>{config.icon}</span>
              }
              title={
                <Space size={8}>
                  <Text>{alert.message}</Text>
                  <Tag color={config.color} style={{ fontSize: 11, lineHeight: '18px' }}>
                    {config.label}
                  </Tag>
                </Space>
              }
              description={
                <Text type="secondary" style={{ fontSize: 12 }}>
                  {dayjs(alert.created_at).fromNow()}
                </Text>
              }
            />
          </List.Item>
        );
      }}
    />
  );
};

export default AlertNotification;
