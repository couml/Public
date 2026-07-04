import React from 'react';
import { Empty } from 'antd';
import { InboxOutlined } from '@ant-design/icons';

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
}

const EmptyState: React.FC<EmptyStateProps> = ({
  icon = <InboxOutlined style={{ fontSize: 64, color: '#bfbfbf' }} />,
  title,
  description,
  action,
}) => {
  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: 320,
        padding: 48,
      }}
    >
      <Empty
        image={icon}
        description={
          <>
            <div style={{ fontSize: 16, fontWeight: 500, color: '#262626', marginBottom: 4 }}>{title}</div>
            {description && <div style={{ color: '#8c8c8c', fontSize: 14 }}>{description}</div>}
          </>
        }
      >
        {action}
      </Empty>
    </div>
  );
};

export default EmptyState;
