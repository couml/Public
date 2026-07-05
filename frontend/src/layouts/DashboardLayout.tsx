import React, { useState } from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import { Layout, Button, Dropdown, Badge, Avatar, Space, Typography, theme } from 'antd';
import {
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  BellOutlined,
  LogoutOutlined,
  UserOutlined,
} from '@ant-design/icons';
import { useAuthStore } from '@/store/authStore';
import Sidebar from '@/layouts/Sidebar';

const { Header, Sider, Content } = Layout;
const { Text } = Typography;

const HeaderRight: React.FC = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const dropdownItems = {
    items: [
      {
        key: 'role',
        label: (
          <Text type="secondary" style={{ fontSize: 12 }}>
            {user?.role === 'admin' ? '管理员' : user?.role === 'it_staff' ? 'IT 支持' : '普通用户'}
          </Text>
        ),
        disabled: true,
      },
      { type: 'divider' as const },
      {
        key: 'logout',
        icon: <LogoutOutlined />,
        label: '退出登录',
        danger: true,
      },
    ],
    onClick: (e: { key: string }) => {
      if (e.key === 'logout') handleLogout();
    },
  };

  return (
    <Space size={20}>
      <Badge count={3} size="small">
        <BellOutlined style={{ fontSize: 18, cursor: 'pointer' }} />
      </Badge>
      <Dropdown menu={dropdownItems} placement="bottomRight">
        <Space style={{ cursor: 'pointer' }}>
          <Avatar size="small" icon={<UserOutlined />} />
          <Text>{user?.full_name || user?.username}</Text>
        </Space>
      </Dropdown>
    </Space>
  );
};

const DashboardLayout: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);
  const { token } = theme.useToken();

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        trigger={null}
        width={240}
        theme="dark"
      >
        <Sidebar />
      </Sider>
      <Layout>
        <Header
          style={{
            background: token.colorBgContainer,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '0 24px',
            boxShadow: '0 1px 4px rgba(0,0,0,0.08)',
            zIndex: 1,
          }}
        >
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
            style={{ fontSize: 16, width: 40, height: 40 }}
          />
          <HeaderRight />
        </Header>
        <Content style={{ padding: 24, minHeight: 'calc(100vh - 64px)', background: token.colorBgLayout }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
};

export default DashboardLayout;
