import React from 'react';
import { Skeleton, Card, Space } from 'antd';

interface LoadingSkeletonProps {
  type: 'card' | 'table' | 'detail' | 'form';
}

const LoadingSkeleton: React.FC<LoadingSkeletonProps> = ({ type }) => {
  switch (type) {
    case 'card':
      return (
        <Card>
          <Skeleton active paragraph={{ rows: 2 }} />
        </Card>
      );

    case 'table':
      return (
        <Card>
          <Skeleton active title paragraph={{ rows: 6 }} />
        </Card>
      );

    case 'detail':
      return (
        <Card>
          <Skeleton active avatar paragraph={{ rows: 1 }} />
          <div style={{ marginTop: 24 }}>
            <Space direction="vertical" style={{ width: '100%' }} size={16}>
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} active title={false} paragraph={{ rows: 1 }} />
              ))}
            </Space>
          </div>
        </Card>
      );

    case 'form':
      return (
        <Card>
          <Space direction="vertical" style={{ width: '100%' }} size={20}>
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i}>
                <Skeleton active title={{ width: 80 }} paragraph={false} />
                <Skeleton.Input active style={{ width: '100%', marginTop: 8 }} />
              </div>
            ))}
            <Skeleton.Button active style={{ width: 100 }} />
          </Space>
        </Card>
      );

    default:
      return <Skeleton active />;
  }
};

export default LoadingSkeleton;
