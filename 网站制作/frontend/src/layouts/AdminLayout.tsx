import React, { useState } from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { Layout, Menu, Button, Typography, Space, theme, MenuProps } from 'antd';
import {
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  DashboardOutlined,
  PrinterOutlined,
  DownloadOutlined,
  TeamOutlined,
  FileSearchOutlined,
  RollbackOutlined,
  UserOutlined,
} from '@ant-design/icons';

const { Header, Sider, Content } = Layout;
const { Text } = Typography;

const adminMenuItems: MenuProps['items'] = [
  {
    key: '/admin',
    icon: <DashboardOutlined />,
    label: '管理仪表盘',
  },
  {
    key: '/admin/printers',
    icon: <PrinterOutlined />,
    label: '打印机管理',
  },
  {
    key: '/admin/drivers',
    icon: <DownloadOutlined />,
    label: '驱动管理',
  },
  {
    key: '/admin/users',
    icon: <TeamOutlined />,
    label: '用户管理',
  },
  {
    key: '/admin/logs',
    icon: <FileSearchOutlined />,
    label: '系统日志',
  },
  { type: 'divider' },
  {
    key: '/',
    icon: <RollbackOutlined />,
    label: '返回主面板',
  },
];

const AdminLayout: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { token } = theme.useToken();

  const selectedKeys = [location.pathname];

  const handleMenuClick: MenuProps['onClick'] = (e) => {
    navigate(e.key);
  };

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
        <div
          style={{
            height: 64,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 8,
            borderBottom: '1px solid rgba(255,255,255,0.1)',
          }}
        >
          <UserOutlined style={{ fontSize: 20, color: '#fff' }} />
          {!collapsed && (
            <span style={{ fontSize: 16, fontWeight: 700, color: '#fff', whiteSpace: 'nowrap' }}>
              管理后台
            </span>
          )}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={selectedKeys}
          items={adminMenuItems}
          onClick={handleMenuClick}
          style={{ borderInlineEnd: 'none' }}
        />
      </Sider>
      <Layout>
        <Header
          style={{
            background: token.colorBgContainer,
            display: 'flex',
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
          <Text strong style={{ marginLeft: 16, fontSize: 16 }}>
            管理员控制台
          </Text>
        </Header>
        <Content style={{ padding: 24, minHeight: 'calc(100vh - 64px)', background: token.colorBgLayout }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
};

export default AdminLayout;
