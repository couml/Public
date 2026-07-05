import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Menu, MenuProps } from 'antd';
import {
  DashboardOutlined,
  PrinterOutlined,
  RobotOutlined,
  FileTextOutlined,
  DownloadOutlined,
  FolderOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import { useAuthStore } from '@/store/authStore';

type MenuItem = Required<MenuProps>['items'][number];

const Sidebar: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);

  const selectedKey = '/' + location.pathname.split('/').filter(Boolean)[0] || '/dashboard';

  const items: MenuItem[] = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: '仪表盘',
    },
    {
      key: '/devices',
      icon: <PrinterOutlined />,
      label: '打印机',
    },
    {
      key: '/diagnosis',
      icon: <RobotOutlined />,
      label: 'AI 诊断',
    },
    {
      key: '/print',
      icon: <FileTextOutlined />,
      label: '文件打印',
    },
    {
      key: '/drivers',
      icon: <DownloadOutlined />,
      label: '驱动程序',
    },
    {
      key: '/documents',
      icon: <FolderOutlined />,
      label: '文档管理',
    },
    { type: 'divider' },
  ];

  if (user && (user.role === 'admin' || user.role === 'it_staff')) {
    items.push({
      key: '/admin',
      icon: <SettingOutlined />,
      label: '管理后台',
    });
  }

  const handleClick: MenuProps['onClick'] = (e) => {
    navigate(e.key);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
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
        <PrinterOutlined style={{ fontSize: 24, color: '#fff' }} />
        <span style={{ fontSize: 18, fontWeight: 700, color: '#fff', whiteSpace: 'nowrap' }}>
          智慧打印
        </span>
      </div>
      <Menu
        theme="dark"
        mode="inline"
        selectedKeys={[selectedKey]}
        items={items}
        onClick={handleClick}
        style={{ flex: 1, borderInlineEnd: 'none' }}
      />
    </div>
  );
};

export default Sidebar;
