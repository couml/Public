import React, { useEffect, useState, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Row,
  Col,
  Card,
  Tabs,
  Table,
  Button,
  Tag,
  Typography,
  Steps,
  Collapse,
  Descriptions,
  Space,
  Badge,
  Tooltip,
  message,
} from 'antd';
import {
  PrinterOutlined,
  WindowsOutlined,
  AppleOutlined,
  LinuxOutlined,
  DownloadOutlined,
  StarOutlined,
  FileTextOutlined,
  QuestionCircleOutlined,
  CheckCircleOutlined,
  ToolOutlined,
} from '@ant-design/icons';
import PageHeader from '@/components/PageHeader';
import EmptyState from '@/components/EmptyState';
import LoadingSkeleton from '@/components/LoadingSkeleton';
import { driversApi } from '@/api/drivers';
import { formatFileSize, formatDate, formatNumber } from '@/utils/format';
import type { DriverPackage, HP136aPage } from '@/types/driver';

const { Title, Text, Paragraph } = Typography;

type Platform = 'windows' | 'macos' | 'linux';

const PLATFORM_CONFIG: Record<Platform, { icon: React.ReactNode; color: string; label: string }> = {
  windows: { icon: <WindowsOutlined />, color: '#00a4ef', label: 'Windows' },
  macos: { icon: <AppleOutlined />, color: '#555555', label: 'macOS' },
  linux: { icon: <LinuxOutlined />, color: '#f5a623', label: 'Linux' },
};

const INSTALL_STEPS: Record<Platform, { title: string; description: string }[]> = {
  windows: [
    { title: '下载驱动', description: '点击上方"驱动下载"标签页中的下载按钮，将驱动安装包保存到本地。' },
    { title: '运行安装程序', description: '双击下载的 .exe 安装文件，按照安装向导提示完成驱动安装。如果弹出用户账户控制（UAC）提示，请点击"是"。' },
    { title: '连接打印机', description: '使用 USB 线缆将打印机连接到电脑，或确保打印机与电脑在同一 Wi-Fi 网络下。Windows 将自动识别打印机。' },
    { title: '测试打印', description: '打开"设置 > 蓝牙和其他设备 > 打印机和扫描仪"，找到已安装的打印机，点击"管理 > 打印测试页"确认驱动安装成功。' },
  ],
  macos: [
    { title: '下载驱动', description: '点击上方"驱动下载"标签页中的下载按钮，下载适用于 macOS 的驱动包（.dmg 格式）。' },
    { title: '安装驱动', description: '双击 .dmg 文件挂载磁盘映像，然后双击其中的 .pkg 安装包，按照安装向导完成安装。' },
    { title: '添加打印机', description: '打开"系统设置 > 打印机与扫描仪"，点击"+"号添加打印机。系统将自动搜索网络中的打印机或通过 USB 连接的打印机。' },
    { title: '测试打印', description: '在打印机列表中选中已添加的打印机，点击"选项与耗材 > 打印测试页"确认驱动安装成功。' },
  ],
  linux: [
    { title: '下载驱动', description: '点击上方"驱动下载"标签页中的下载按钮，下载适用于 Linux 的驱动包。' },
    { title: '安装驱动（Debian/Ubuntu）', description: '使用命令 sudo dpkg -i <驱动包名>.deb 安装 .deb 格式驱动。如有依赖问题，执行 sudo apt-get install -f 修复。' },
    { title: '安装驱动（RHEL/Fedora）', description: '使用命令 sudo rpm -ivh <驱动包名>.rpm 安装 .rpm 格式驱动，或使用 sudo dnf install <驱动包名>.rpm。' },
    { title: '配置并测试', description: '使用 CUPS 管理界面（http://localhost:631）添加打印机。安装完成后执行 lp -d <打印机名> /usr/share/cups/data/testprint 测试打印。' },
  ],
};

const FAQ_ITEMS = [
  {
    question: '驱动安装失败怎么办？',
    answer: '请尝试以下步骤：1) 确保下载的驱动版本与您的操作系统匹配；2) 安装前暂时关闭杀毒软件；3) 以管理员权限运行安装程序（Windows：右键选择"以管理员身份运行"）；4) 卸载旧版本驱动后重新安装；5) 尝试使用兼容模式安装。如果以上方法均无效，请联系技术支持。',
  },
  {
    question: '打印机无法被电脑识别？',
    answer: '常见解决方案：1) 检查 USB 线缆连接是否牢固，尝试更换 USB 端口或线缆；2) 确保打印机电源已开启且处于就绪状态；3) 在设备管理器中查看是否有未识别设备（带黄色感叹号）；4) 重启打印机和电脑；5) 对于网络打印机，检查 IP 地址和网络连接是否正常，尝试 ping 打印机 IP。',
  },
  {
    question: '打印出现乱码怎么办？',
    answer: '可能原因及解决方法：1) 驱动不匹配 —— 请确认安装了正确的打印机型号驱动；2) 打印队列堵塞 —— 清空打印队列后重新打印；3) 数据线问题 —— 更换 USB 线缆或尝试其他端口；4) 应用软件问题 —— 尝试在其他应用中打印同一文档，或更新应用程序；5) 打印机固件问题 —— 更新打印机固件至最新版本。',
  },
  {
    question: '扫描功能不可用怎么办？',
    answer: '请检查：1) 确认打印机支持扫描功能（多功能一体机）；2) 安装完整的驱动套件（不仅打印驱动，还需扫描驱动）；3) Windows 用户可打开"Windows 传真和扫描"或"Windows 扫描"应用测试；4) 确保扫描服务（Windows Image Acquisition）已启动；5) 尝试使用第三方扫描软件（如 NAPS2、VueScan）作为替代方案。',
  },
  {
    question: 'Mac 系统提示"无法验证开发者"？',
    answer: '这是 macOS 的安全机制。解决方法：1) 打开"系统设置 > 隐私与安全性"；2) 在页面底部找到被阻止的驱动安装程序；3) 点击"仍要打开"按钮确认运行。或者，在 Finder 中找到安装程序文件，右键（或 Control+点击）选择"打开"即可绕过验证。',
  },
  {
    question: '更新驱动后打印机无法工作？',
    answer: '建议：1) 先尝试回滚到之前正常的驱动版本（可在本页面下载历史版本）；2) 完全卸载当前驱动后重新启动电脑，再安装新驱动；3) 清除打印队列中的所有待处理任务；4) 查看官方驱动发布说明（Release Notes）中的已知问题；5) 如为重大更新，考虑等待后续补丁版本。',
  },
];

const DriverDetailPage: React.FC = () => {
  const { brand, model } = useParams<{ brand: string; model: string }>();
  const navigate = useNavigate();
  const decodedBrand = decodeURIComponent(brand || '');
  const decodedModel = decodeURIComponent(model || '');

  const [drivers, setDrivers] = useState<DriverPackage[]>([]);
  const [loading, setLoading] = useState(true);
  const [hpData, setHpData] = useState<HP136aPage | null>(null);
  const [expandedChangelogs, setExpandedChangelogs] = useState<Set<string>>(new Set());

  const isHP136a = decodedBrand === 'HP' && decodedModel === 'Laser MFP 136a';

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const data = await driversApi.list({
          brand: decodedBrand,
          model: decodedModel,
          page_size: 100,
        });
        setDrivers(data.items);

        if (decodedBrand === 'HP' && decodedModel === 'Laser MFP 136a') {
          try {
            const hp = await driversApi.getHP136a();
            setHpData(hp);
          } catch {
            // HP 136a specific data not available
          }
        }
      } catch (error) {
        console.error('Failed to fetch driver detail:', error);
        setDrivers([]);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [decodedBrand, decodedModel]);

  const driversByPlatform = useMemo(() => {
    const groups: Record<Platform, DriverPackage[]> = {
      windows: [],
      macos: [],
      linux: [],
    };
    for (const d of drivers) {
      if (d.os_platform in groups) {
        groups[d.os_platform as Platform].push(d);
      }
    }
    // Sort each group by version descending
    for (const key of Object.keys(groups) as Platform[]) {
      groups[key].sort((a, b) => b.version.localeCompare(a.version, undefined, { numeric: true }));
    }
    return groups;
  }, [drivers]);

  const handleDownload = (driverId: string) => {
    const url = driversApi.getDownloadUrl(driverId);
    window.open(url, '_blank');
    message.success('开始下载驱动...');
  };

  const toggleChangelog = (id: string) => {
    setExpandedChangelogs((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const driverColumns = [
    {
      title: '平台',
      dataIndex: 'os_platform',
      key: 'os_platform',
      width: 100,
      render: (platform: Platform) => {
        const config = PLATFORM_CONFIG[platform];
        return config ? (
          <Tag icon={config.icon} color={config.color}>{config.label}</Tag>
        ) : platform;
      },
    },
    {
      title: '版本',
      dataIndex: 'version',
      key: 'version',
      width: 120,
      render: (v: string) => <Tag color="blue">v{v}</Tag>,
    },
    {
      title: '文件大小',
      dataIndex: 'file_size',
      key: 'file_size',
      width: 100,
      render: (size: number) => formatFileSize(size),
    },
    {
      title: '发布日期',
      dataIndex: 'release_date',
      key: 'release_date',
      width: 140,
      render: (date: string) => formatDate(date),
    },
    {
      title: '更新日志',
      dataIndex: 'changelog',
      key: 'changelog',
      render: (changelog: string | null, record: DriverPackage) => {
        if (!changelog) return <Text type="secondary">-</Text>;
        const isExpanded = expandedChangelogs.has(record.id);
        return (
          <div>
            {isExpanded ? (
              <div style={{ whiteSpace: 'pre-wrap', fontSize: 13, lineHeight: 1.6, marginBottom: 4 }}>
                {changelog}
              </div>
            ) : (
              <Text ellipsis style={{ maxWidth: 300, display: 'inline-block' }}>
                {changelog}
              </Text>
            )}
            <Button
              type="link"
              size="small"
              onClick={() => toggleChangelog(record.id)}
              style={{ padding: 0 }}
            >
              {isExpanded ? '收起' : '展开'}
            </Button>
          </div>
        );
      },
    },
    {
      title: '下载',
      key: 'action',
      width: 100,
      render: (_: unknown, record: DriverPackage) => (
        <Button
          type="primary"
          icon={<DownloadOutlined />}
          size="small"
          onClick={() => handleDownload(record.id)}
        >
          下载
        </Button>
      ),
    },
  ];

  const renderDriversTab = () => {
    const platformKeys: Platform[] = ['windows', 'macos', 'linux'];
    const hasDrivers = platformKeys.some((p) => driversByPlatform[p].length > 0);

    if (!hasDrivers) {
      return (
        <EmptyState
          title="暂无驱动"
          description="该型号暂无可用的驱动程序"
        />
      );
    }

    return (
      <div>
        {platformKeys.map((platform) => {
          const list = driversByPlatform[platform];
          if (list.length === 0) return null;
          const config = PLATFORM_CONFIG[platform];
          return (
            <div key={platform} style={{ marginBottom: 24 }}>
              <Title level={5} style={{ marginBottom: 12 }}>
                <Space>
                  {config.icon}
                  {config.label}
                  <Tag>{list.length} 个版本</Tag>
                </Space>
              </Title>
              <Table
                dataSource={list}
                columns={driverColumns}
                rowKey="id"
                pagination={false}
                size="middle"
                style={{ background: '#fff' }}
              />
            </div>
          );
        })}
      </div>
    );
  };

  const renderInstallGuideTab = () => {
    const platforms: { key: Platform; label: string }[] = [
      { key: 'windows', label: 'Windows' },
      { key: 'macos', label: 'macOS' },
      { key: 'linux', label: 'Linux' },
    ];

    return (
      <div>
        {platforms.map(({ key, label }) => {
          const steps = hpData?.install_guides?.[key]
            ? [{ title: '专用安装指南', description: hpData.install_guides[key] }]
            : INSTALL_STEPS[key];

          return (
            <Card
              key={key}
              title={
                <Space>
                  {PLATFORM_CONFIG[key].icon}
                  {label}
                </Space>
              }
              style={{ marginBottom: 16 }}
            >
              <Steps
                direction="vertical"
                size="small"
                current={-1}
                items={steps.map((step) => ({
                  title: step.title,
                  description: step.description,
                }))}
              />
            </Card>
          );
        })}
      </div>
    );
  };

  const renderFaqTab = () => {
    const items = hpData?.faqs
      ? hpData.faqs.map((faq, i) => ({
          key: String(i),
          label: <Space><QuestionCircleOutlined />{faq.question}</Space>,
          children: <Paragraph style={{ whiteSpace: 'pre-wrap', margin: 0 }}>{faq.answer}</Paragraph>,
        }))
      : FAQ_ITEMS.map((faq, i) => ({
          key: String(i),
          label: <Space><QuestionCircleOutlined />{faq.question}</Space>,
          children: <Paragraph style={{ whiteSpace: 'pre-wrap', margin: 0 }}>{faq.answer}</Paragraph>,
        }));

    return <Collapse accordion items={items} />;
  };

  const renderHPSpecialSection = () => {
    if (!isHP136a || !hpData) return null;

    return (
      <>
        {/* Firmware Section */}
        {hpData.drivers.some((d) => d.os_platform === 'windows') && (
          <Card
            title={<Space><ToolOutlined />固件更新</Space>}
            style={{ marginBottom: 16 }}
            type="inner"
          >
            <Descriptions size="small" column={2}>
              <Descriptions.Item label="当前固件版本">
                <Tag color="green">v{hpData.drivers[0]?.version || '-'}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="发布日期">
                {formatDate(hpData.drivers[0]?.release_date || '')}
              </Descriptions.Item>
            </Descriptions>
            <Button
              type="primary"
              icon={<DownloadOutlined />}
              onClick={() => {
                const winDriver = hpData.drivers.find((d) => d.os_platform === 'windows');
                if (winDriver) handleDownload(winDriver.id);
              }}
              style={{ marginTop: 8 }}
            >
              下载最新固件
            </Button>
          </Card>
        )}

        {/* Manuals Section */}
        {hpData.manuals && hpData.manuals.length > 0 && (
          <Card
            title={<Space><FileTextOutlined />用户手册下载</Space>}
            style={{ marginBottom: 16 }}
            type="inner"
          >
            {hpData.manuals.map((manual, i) => (
              <div
                key={i}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '8px 0',
                  borderBottom: i < hpData.manuals.length - 1 ? '1px solid #f0f0f0' : 'none',
                }}
              >
                <Space>
                  <FileTextOutlined />
                  <Text>{manual.title}</Text>
                  {manual.size && <Tag>{manual.size}</Tag>}
                </Space>
                <Button
                  type="link"
                  icon={<DownloadOutlined />}
                  onClick={() => {
                    if (manual.url) window.open(manual.url, '_blank');
                  }}
                >
                  下载
                </Button>
              </div>
            ))}
          </Card>
        )}
      </>
    );
  };

  if (loading) {
    return (
      <div className="page-container">
        <PageHeader
          title={`${decodedBrand} ${decodedModel}`}
          breadcrumb={[
            { title: '驱动下载', path: '/drivers' },
            { title: decodedBrand },
            { title: decodedModel },
          ]}
        />
        <LoadingSkeleton type="detail" />
      </div>
    );
  }

  return (
    <div className="page-container">
      <PageHeader
        title={`${decodedBrand} ${decodedModel}`}
        breadcrumb={[
          { title: '驱动下载', path: '/drivers' },
          { title: decodedBrand },
          { title: decodedModel },
        ]}
      />

      {/* Hero Section */}
      <Card style={{ marginBottom: 24, borderRadius: 12, overflow: 'hidden' }}>
        <Row align="middle" gutter={32}>
          <Col flex="160px" style={{ textAlign: 'center' }}>
            <div
              style={{
                width: 140,
                height: 140,
                borderRadius: 16,
                background: 'linear-gradient(135deg, #e6f4ff 0%, #bae0ff 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                position: 'relative',
              }}
            >
              <PrinterOutlined style={{ fontSize: 64, color: '#1677ff' }} />
              {isHP136a && (
                <div style={{ position: 'absolute', top: -4, right: -4 }}>
                  <Tooltip title="推荐型号">
                    <StarOutlined style={{ fontSize: 24, color: '#faad14' }} />
                  </Tooltip>
                </div>
              )}
            </div>
          </Col>
          <Col flex="auto">
            <Space align="center" style={{ marginBottom: 4 }}>
              <Title level={3} style={{ margin: 0 }}>{decodedModel}</Title>
              {isHP136a && (
                <Badge.Ribbon text="推荐" color="#faad14" style={{ position: 'static' }} />
              )}
            </Space>
            <div style={{ marginBottom: 8 }}>
              <Text type="secondary" style={{ fontSize: 15 }}>
                品牌：{decodedBrand}
              </Text>
            </div>
            {drivers.length > 0 && (
              <div style={{ marginBottom: 12 }}>
                <Tag color="blue" style={{ fontSize: 14, padding: '2px 12px' }}>
                  最新版本: v{drivers[0]?.version}
                </Tag>
                <Text type="secondary" style={{ fontSize: 13 }}>
                  共 {drivers.length} 个驱动包 · 发布于 {formatDate(drivers[0]?.release_date)}
                </Text>
              </div>
            )}
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              {(['windows', 'macos', 'linux'] as Platform[]).map((p) => {
                const count = driversByPlatform[p].length;
                return (
                  <Tag
                    key={p}
                    icon={PLATFORM_CONFIG[p].icon}
                    color={count > 0 ? 'blue' : 'default'}
                  >
                    {PLATFORM_CONFIG[p].label} {count > 0 ? `(${count})` : ''}
                  </Tag>
                );
              })}
            </div>
          </Col>
        </Row>
      </Card>

      {/* Tabs */}
      <Card style={{ borderRadius: 12 }}>
        <Tabs
          defaultActiveKey="drivers"
          items={[
            {
              key: 'drivers',
              label: <span><DownloadOutlined /> 驱动下载</span>,
              children: renderDriversTab(),
            },
            {
              key: 'install',
              label: <span><ToolOutlined /> 安装指南</span>,
              children: renderInstallGuideTab(),
            },
            {
              key: 'faq',
              label: <span><QuestionCircleOutlined /> 常见问题</span>,
              children: renderFaqTab(),
            },
          ]}
        />
      </Card>

      {/* HP 136a Special Section */}
      {renderHPSpecialSection()}

      {drivers.length === 0 && !loading && (
        <EmptyState
          title="未找到驱动数据"
          description={`未找到 ${decodedBrand} ${decodedModel} 的驱动信息`}
          action={
            <Button onClick={() => navigate('/drivers')}>返回驱动列表</Button>
          }
        />
      )}
    </div>
  );
};

export default DriverDetailPage;
