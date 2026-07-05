import React, { useEffect, useState, useMemo, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Row,
  Col,
  Card,
  Pagination,
  Select,
  Avatar,
  Tag,
  Button,
  Typography,
  Space,
  Badge,
} from 'antd';
import {
  PrinterOutlined,
  WindowsOutlined,
  AppleOutlined,
  LinuxOutlined,
  DownloadOutlined,
  StarOutlined,
} from '@ant-design/icons';
import PageHeader from '@/components/PageHeader';
import SearchBar from '@/components/SearchBar';
import EmptyState from '@/components/EmptyState';
import LoadingSkeleton from '@/components/LoadingSkeleton';
import { driversApi } from '@/api/drivers';
import { PRINTER_BRANDS } from '@/utils/constants';
import { formatNumber } from '@/utils/format';
import type { DriverPackage } from '@/types/driver';

const { Title, Text, Paragraph } = Typography;

const OS_OPTIONS = [
  { label: '全部平台', value: '' },
  { label: 'Windows', value: 'windows' },
  { label: 'macOS', value: 'macos' },
  { label: 'Linux', value: 'linux' },
];

const PLATFORM_CONFIG: Record<string, { icon: React.ReactNode; color: string; label: string }> = {
  windows: { icon: <WindowsOutlined />, color: '#00a4ef', label: 'Windows' },
  macos: { icon: <AppleOutlined />, color: '#555555', label: 'macOS' },
  linux: { icon: <LinuxOutlined />, color: '#f5a623', label: 'Linux' },
};

function compareVersions(a: string, b: string): number {
  const pa = a.replace(/^v/i, '').split('.').map(Number);
  const pb = b.replace(/^v/i, '').split('.').map(Number);
  const len = Math.max(pa.length, pb.length);
  for (let i = 0; i < len; i++) {
    const na = pa[i] || 0;
    const nb = pb[i] || 0;
    if (na > nb) return 1;
    if (na < nb) return -1;
  }
  return 0;
}

interface GroupedDriver {
  brand: string;
  model: string;
  latestVersion: string;
  platforms: string[];
  totalDownloads: number;
  ids: string[];
}

const DriverListPage: React.FC = () => {
  const navigate = useNavigate();
  const [drivers, setDrivers] = useState<DriverPackage[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [brand, setBrand] = useState('');
  const [os, setOs] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const pageSize = 12;

  const fetchDrivers = useCallback(async () => {
    setLoading(true);
    try {
      const data = await driversApi.list({
        search: search || undefined,
        brand: brand || undefined,
        os: os || undefined,
        page,
        page_size: pageSize,
      });
      setDrivers(data.items);
      setTotal(data.total);
    } catch (error) {
      console.error('Failed to fetch drivers:', error);
      setDrivers([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [search, brand, os, page]);

  useEffect(() => {
    fetchDrivers();
  }, [fetchDrivers]);

  const groupedDrivers = useMemo<GroupedDriver[]>(() => {
    const map = new Map<string, GroupedDriver>();
    for (const d of drivers) {
      const key = `${d.brand}|||${d.model}`;
      const existing = map.get(key);
      if (existing) {
        if (!existing.platforms.includes(d.os_platform)) {
          existing.platforms.push(d.os_platform);
        }
        existing.totalDownloads += d.download_count;
        existing.ids.push(d.id);
        if (compareVersions(d.version, existing.latestVersion) > 0) {
          existing.latestVersion = d.version;
        }
      } else {
        map.set(key, {
          brand: d.brand,
          model: d.model,
          latestVersion: d.version,
          platforms: [d.os_platform],
          totalDownloads: d.download_count,
          ids: [d.id],
        });
      }
    }
    // Sort: HP 136a first, then by total downloads descending
    return Array.from(map.values()).sort((a, b) => {
      if (a.brand === 'HP' && a.model === 'Laser MFP 136a') return -1;
      if (b.brand === 'HP' && b.model === 'Laser MFP 136a') return 1;
      return b.totalDownloads - a.totalDownloads;
    });
  }, [drivers]);

  const handleSearch = useCallback((value: string) => {
    setSearch(value);
    setPage(1);
  }, []);

  const handleBrandChange = useCallback((value: string) => {
    setBrand(value);
    setPage(1);
  }, []);

  const handleOsChange = useCallback((value: string) => {
    setOs(value);
    setPage(1);
  }, []);

  const handleNavigate = useCallback(
    (brandName: string, modelName: string) => {
      navigate(`/drivers/${encodeURIComponent(brandName)}/${encodeURIComponent(modelName)}`);
    },
    [navigate],
  );

  const renderHP136aCard = () => {
    const hpEntry = groupedDrivers.find((d) => d.brand === 'HP' && d.model === 'Laser MFP 136a');
    if (!hpEntry) return null;

    return (
      <Badge.Ribbon
        text={<span><StarOutlined /> 推荐</span>}
        color="#faad14"
        style={{ fontWeight: 600 }}
      >
        <Card
          hoverable
          style={{
            marginBottom: 24,
            borderColor: '#faad14',
            borderWidth: 2,
            boxShadow: '0 2px 12px rgba(250, 173, 20, 0.15)',
          }}
          onClick={() => handleNavigate(hpEntry.brand, hpEntry.model)}
        >
          <Row align="middle" gutter={24}>
            <Col flex="120px" style={{ textAlign: 'center' }}>
              <div
                style={{
                  width: 100,
                  height: 100,
                  borderRadius: 12,
                  background: 'linear-gradient(135deg, #fff7e6 0%, #ffe58f 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <PrinterOutlined style={{ fontSize: 48, color: '#d48806' }} />
              </div>
            </Col>
            <Col flex="auto">
              <Title level={4} style={{ marginBottom: 4 }}>
                HP Laser MFP 136a
              </Title>
              <Text type="secondary" style={{ fontSize: 14 }}>
                一站式驱动下载 —— 包含驱动、固件、说明书及安装指南
              </Text>
              <div style={{ marginTop: 12 }}>
                <Tag color="blue" style={{ fontSize: 13, padding: '2px 10px' }}>
                  最新版本: v{hpEntry.latestVersion}
                </Tag>
                {hpEntry.platforms.map((p) => (
                  <Tag key={p} icon={PLATFORM_CONFIG[p]?.icon} style={{ fontSize: 13 }}>
                    {PLATFORM_CONFIG[p]?.label}
                  </Tag>
                ))}
                <Text type="secondary" style={{ fontSize: 13, marginLeft: 8 }}>
                  <DownloadOutlined /> {formatNumber(hpEntry.totalDownloads)} 次下载
                </Text>
              </div>
            </Col>
            <Col>
              <Button type="primary" size="large" icon={<DownloadOutlined />}>
                查看详情
              </Button>
            </Col>
          </Row>
        </Card>
      </Badge.Ribbon>
    );
  };

  const renderDriverCard = (item: GroupedDriver) => {
    const isHP136a = item.brand === 'HP' && item.model === 'Laser MFP 136a';
    if (isHP136a) return null; // Already rendered as hero card

    return (
      <Col span={6} key={`${item.brand}-${item.model}`} style={{ marginBottom: 16 }}>
        <Card
          hoverable
          style={{ height: '100%', borderRadius: 8 }}
          onClick={() => handleNavigate(item.brand, item.model)}
          actions={[
            <Button
              type="link"
              icon={<DownloadOutlined />}
              key="detail"
              onClick={(e) => {
                e.stopPropagation();
                handleNavigate(item.brand, item.model);
              }}
            >
              查看详情
            </Button>,
          ]}
        >
          <div style={{ marginBottom: 16, display: 'flex', alignItems: 'center', gap: 12 }}>
            <Avatar
              size={48}
              shape="square"
              style={{
                backgroundColor: '#1677ff',
                borderRadius: 8,
                fontSize: 20,
                fontWeight: 600,
              }}
            >
              {item.brand[0]}
            </Avatar>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontWeight: 600, fontSize: 14, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {item.brand}
              </div>
              <Text type="secondary" style={{ fontSize: 13, display: 'block', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {item.model}
              </Text>
            </div>
          </div>

          <div style={{ marginBottom: 12 }}>
            <Tag color="blue">v{item.latestVersion}</Tag>
            <div style={{ marginTop: 8, display: 'flex', gap: 4, flexWrap: 'wrap' }}>
              {item.platforms.sort().map((p) => {
                const config = PLATFORM_CONFIG[p];
                return config ? (
                  <Tag key={p} icon={config.icon} color={p === 'windows' ? 'blue' : p === 'macos' ? 'default' : 'orange'}>
                    {config.label}
                  </Tag>
                ) : null;
              })}
            </div>
          </div>

          <Text type="secondary" style={{ fontSize: 12 }}>
            <DownloadOutlined /> {formatNumber(item.totalDownloads)} 次下载
          </Text>
        </Card>
      </Col>
    );
  };

  const otherDrivers = useMemo(
    () => groupedDrivers.filter((d) => !(d.brand === 'HP' && d.model === 'Laser MFP 136a')),
    [groupedDrivers],
  );

  return (
    <div className="page-container">
      <PageHeader title="驱动下载中心" />

      <Card style={{ marginBottom: 24 }}>
        <Space wrap size="middle">
          <SearchBar onSearch={handleSearch} placeholder="搜索品牌或型号..." />

          <Select
            value={brand || undefined}
            onChange={handleBrandChange}
            placeholder="选择品牌"
            allowClear
            style={{ width: 140 }}
            options={[
              { label: '全部品牌', value: '' },
              ...PRINTER_BRANDS.map((b) => ({ label: b, value: b })),
            ]}
            onClear={() => handleBrandChange('')}
          />

          <Select
            value={os || undefined}
            onChange={handleOsChange}
            style={{ width: 130 }}
            options={OS_OPTIONS.map((o) => ({ label: o.label, value: o.value || undefined }))}
          />
        </Space>
      </Card>

      {loading ? (
        <Row gutter={[16, 16]}>
          {Array.from({ length: 8 }).map((_, i) => (
            <Col span={6} key={i}>
              <LoadingSkeleton type="card" />
            </Col>
          ))}
        </Row>
      ) : groupedDrivers.length === 0 ? (
        <EmptyState title="暂无驱动数据" description="请尝试调整筛选条件" />
      ) : (
        <>
          {renderHP136aCard()}

          <Row gutter={[16, 16]}>
            {otherDrivers.map(renderDriverCard)}
          </Row>

          {total > pageSize && (
            <div style={{ marginTop: 24, textAlign: 'center' }}>
              <Pagination
                current={page}
                pageSize={pageSize}
                total={total}
                onChange={(p) => setPage(p)}
                showSizeChanger={false}
                showTotal={(t) => `共 ${t} 个驱动包`}
              />
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default DriverListPage;
