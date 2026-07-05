import React from 'react';
import { Card, Skeleton, Typography } from 'antd';

const { Text, Title } = Typography;

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color?: string;
  loading?: boolean;
}

const StatCard: React.FC<StatCardProps> = ({ title, value, icon, color = '#1677ff', loading = false }) => {
  if (loading) {
    return (
      <Card>
        <Skeleton active paragraph={{ rows: 1 }} title={{ width: '60%' }} />
      </Card>
    );
  }

  return (
    <Card hoverable>
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12 }}>
        <div
          style={{
            width: 56,
            height: 56,
            borderRadius: '50%',
            background: `${color}15`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color,
            fontSize: 24,
          }}
        >
          {icon}
        </div>
        <Title level={3} style={{ margin: 0, color }}>
          {value}
        </Title>
        <Text type="secondary">{title}</Text>
      </div>
    </Card>
  );
};

export default StatCard;
