import React, { useEffect, useMemo, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Row,
  Col,
  Card,
  Table,
  Input,
  Select,
  Segmented,
  Progress,
  Button,
  Space,
  Typography,
  Pagination,
} from 'antd';
import {
  EyeOutlined,
  AppstoreOutlined,
  UnorderedListOutlined,
} from '@ant-design/icons';
import StatusBadge from '@/components/StatusBadge';
import { useDeviceStore } from '@/store/deviceStore';
import type { Printer } from '@/types/device';

const { Search } = Input;
const { Text } = Typography;

type ViewMode = 'card' | 'table';

const PAGE_SIZE = 12;

const DeviceListPage: React.FC = () => {
  const navigate = useNavigate();
  const { devices, totalDevices, isLoading, fetchDevices } = useDeviceStore();
  const [viewMode, setViewMode] = useState<ViewMode>('card');
  const [searchText, setSearchText] = useState('');
  const [brandFilter, setBrandFilter] = useState<string | undefined>();
  const [statusFilter, setStatusFilter] = useState<string | undefined>();
  const [page, setPage] = useState(1);

  useEffect(() => {
    fetchDevices({
      search: searchText || undefined,
      brand: brandFilter,
      status: statusFilter,
      page,
      page_size: PAGE_SIZE,
    });
  }, [fetchDevices, searchText, brandFilter, statusFilter, page]);

  const brands = useMemo(() => {
    const brandSet = new Set(devices.map((d) => d.brand).filter(Boolean));
    return Array.from(brandSet).sort();
  }, [devices]);

  const handleSearch = useCallback((value: string) => {
    setSearchText(value);
    setPage(1);
  }, []);

  const handleBrandChange = useCallback((value: string | undefined) => {
    setBrandFilter(value);
    setPage(1);
  }, []);

  const handleStatusChange = useCallback((value: string | undefined) => {
    setStatusFilter(value);
    setPage(1);
  }, []);

  const columns = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      ellipsis: true,
    },
    {
      title: '品牌',
      dataIndex: 'brand',
      key: 'brand',
      width: 100,
    },
    {
      title: '型号',
      dataIndex: 'model',
      key: 'model',
      width: 120,
    },
    {
      title: 'IP 地址',
      dataIndex: 'ip_address',
      key: 'ip_address',
      width: 140,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 90,
      render: (status: Printer['status']) => <StatusBadge status={status} />,
    },
    {
      title: '位置',
      dataIndex: 'location',
      key: 'location',
      width: 120,
      render: (v: string | null) => v || '-',
    },
    {
      title: '操作',
      key: 'actions',
      width: 80,
      render: (_: unknown, record: Printer) => (
        <Button
          type="link"
          size="small"
          icon={<EyeOutlined />}
          onClick={(e) => {
            e.stopPropagation();
            navigate(`/devices/${record.id}`);
          }}
        >
          详情
        </Button>
      ),
    },
  ];

  return (
    <div className="page-container">
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 16,
          flexWrap: 'wrap',
          gap: 12,
        }}
      >
        <Space size="middle" wrap>
          <Search
            placeholder="搜索设备名称或 IP"
            allowClear
            onSearch={handleSearch}
            style={{ width: 260 }}
          />
          <Select
            placeholder="品牌筛选"
            allowClear
            style={{ width: 140 }}
            value={brandFilter}
            onChange={handleBrandChange}
            options={brands.map((b) => ({ label: b, value: b }))}
          />
          <Select
            placeholder="状态筛选"
            allowClear
            style={{ width: 120 }}
            value={statusFilter}
            onChange={handleStatusChange}
            options={[
              { label: '在线', value: 'online' },
              { label: '离线', value: 'offline' },
              { label: '繁忙', value: 'busy' },
              { label: '故障', value: 'error' },
            ]}
          />
        </Space>
        <Segmented
          value={viewMode}
          onChange={(v) => setViewMode(v as ViewMode)}
          options={[
            {
              label: (
                <>
                  <AppstoreOutlined /> 卡片
                </>
              ),
              value: 'card',
            },
            {
              label: (
                <>
                  <UnorderedListOutlined /> 列表
                </>
              ),
              value: 'table',
            },
          ]}
        />
      </div>

      {viewMode === 'card' ? (
        <>
          <Row gutter={[16, 16]}>
            {devices.map((device) => (
              <Col key={device.id} span={6} xl={6} lg={8} md={12} sm={24}>
                <Card
                  hoverable
                  onClick={() => navigate(`/devices/${device.id}`)}
                  style={{ height: '100%' }}
                >
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      marginBottom: 12,
                    }}
                  >
                    <Text strong style={{ fontSize: 15 }} ellipsis>
                      {device.name}
                    </Text>
                    <StatusBadge status={device.status} size="small" />
                  </div>
                  <div style={{ marginBottom: 8 }}>
                    <Text type="secondary">
                      {device.brand} {device.model}
                    </Text>
                  </div>
                  <div style={{ marginBottom: 4 }}>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      IP: {device.ip_address}
                    </Text>
                  </div>
                  <div style={{ marginBottom: 12 }}>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      位置: {device.location || '未设置'}
                    </Text>
                  </div>
                  <div style={{ marginBottom: 4 }}>
                    <Text style={{ fontSize: 12 }}>墨粉余量</Text>
                    <Progress
                      percent={device.toner_level}
                      size="small"
                      status={
                        device.toner_level < 10 ? 'exception' : undefined
                      }
                    />
                  </div>
                  <div style={{ marginBottom: 12 }}>
                    <Text style={{ fontSize: 12 }}>纸张余量</Text>
                    <Progress
                      percent={device.paper_level}
                      size="small"
                      status={
                        device.paper_level < 10 ? 'exception' : undefined
                      }
                    />
                  </div>
                  <Button
                    type="primary"
                    size="small"
                    icon={<EyeOutlined />}
                    onClick={(e) => {
                      e.stopPropagation();
                      navigate(`/devices/${device.id}`);
                    }}
                    block
                  >
                    查看详情
                  </Button>
                </Card>
              </Col>
            ))}
            {!isLoading && devices.length === 0 && (
              <Col span={24}>
                <div
                  style={{
                    textAlign: 'center',
                    padding: 64,
                    color: '#999',
                  }}
                >
                  暂无设备数据
                </div>
              </Col>
            )}
          </Row>
          <div style={{ marginTop: 16, textAlign: 'center' }}>
            <Pagination
              current={page}
              pageSize={PAGE_SIZE}
              total={totalDevices}
              showSizeChanger
              showTotal={(total) => `共 ${total} 台设备`}
              onChange={(p) => setPage(p)}
            />
          </div>
        </>
      ) : (
        <Table
          columns={columns}
          dataSource={devices}
          rowKey="id"
          loading={isLoading}
          pagination={{
            current: page,
            pageSize: PAGE_SIZE,
            total: totalDevices,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 台设备`,
            onChange: (p) => setPage(p),
          }}
          onRow={(record) => ({
            onClick: () => navigate(`/devices/${record.id}`),
            style: { cursor: 'pointer' },
          })}
        />
      )}
    </div>
  );
};

export default DeviceListPage;
