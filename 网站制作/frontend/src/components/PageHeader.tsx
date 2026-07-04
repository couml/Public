import React from 'react';
import { Breadcrumb, Typography, Space } from 'antd';
import { useNavigate } from 'react-router-dom';

const { Title } = Typography;

interface BreadcrumbItem {
  title: string;
  path?: string;
}

interface PageHeaderProps {
  title: string;
  breadcrumb?: BreadcrumbItem[];
  extra?: React.ReactNode;
}

const PageHeader: React.FC<PageHeaderProps> = ({ title, breadcrumb, extra }) => {
  const navigate = useNavigate();

  const breadcrumbItems = breadcrumb?.map((item) => ({
    title: item.path ? (
      <a onClick={() => navigate(item.path!)} style={{ cursor: 'pointer' }}>
        {item.title}
      </a>
    ) : (
      item.title
    ),
  }));

  return (
    <div style={{ marginBottom: 24 }}>
      {breadcrumb && breadcrumb.length > 0 && (
        <Breadcrumb items={breadcrumbItems} style={{ marginBottom: 8 }} />
      )}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: 12,
        }}
      >
        <Title level={4} style={{ margin: 0 }}>
          {title}
        </Title>
        {extra && <Space wrap>{extra}</Space>}
      </div>
    </div>
  );
};

export default PageHeader;
