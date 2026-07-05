import React, { useEffect, useMemo, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Row,
  Col,
  Card,
  Descriptions,
  Tabs,
  Table,
  Button,
  Progress,
  Space,
  Breadcrumb,
  Spin,
  Tag,
  message,
  Typography,
} from 'antd';
import {
  HomeOutlined,
  ReloadOutlined,
  CheckCircleOutlined,
  WifiOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import dayjs from 'dayjs';
import StatusBadge from '@/components/StatusBadge';
import { useDeviceStore } from '@/store/deviceStore';
import { useWebSocket } from '@/hooks/useWebSocket';
import { devicesApi } from '@/api/devices';
import type {
  PrinterStatusLog,
  PrinterAlert,
  AlertSeverity,
  DeviceStatusUpdate,
} from '@/types/device';

const { Text } = Typography;

const severityColorMap: Record<string, string> = {
  info: 'blue',
  warning: 'orange',
  critical: 'red',
};

const severityLabelMap: Record<AlertSeverity, string> = {
  info: '信息',
  warning: '警告',
  critical: '严重',
};

const alertTypeLabels: Record<string, string> = {
  paper_out: '缺纸',
  paper_jam: '卡纸',
  paper_low: '纸张不足',
  toner_low: '墨粉不足',
  toner_empty: '墨粉耗尽',
  offline: '离线',
  service_required: '需要维护',
  fuser_warning: '定影警告',
  drum_low: '硒鼓不足',
};

const queueStatusMap: Record<string, { color: string; text: string }> = {
  queued: { color: 'default', text: '排队中' },
  printing: { color: 'processing', text: '打印中' },
  completed: { color: 'success', text: '已完成' },
  failed: { color: 'error', text: '失败' },
  cancelled: { color: 'default', text: '已取消' },
};

const DeviceDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { selectedDevice, fetchDevice, updateStatus } = useDeviceStore();

  const [logs, setLogs] = useState<PrinterStatusLog[]>([]);
  const [alerts, setAlerts] = useState<PrinterAlert[]>([]);
  const [queue, setQueue] = useState<Record<string, unknown>[]>([]);
  const [loadingLogs, setLoadingLogs] = useState(false);
  const [loadingAlerts, setLoadingAlerts] = useState(false);
  const [loadingQueue, setLoadingQueue] = useState(false);
  const [latency, setLatency] = useState<number | null>(null);

  // WebSocket message handler
  const handleWsMessage = useCallback(
    (data: DeviceStatusUpdate & { type?: string; response_time_ms?: number }) => {
      if (!id) return;
      updateStatus({
        id,
        status: data.status,
        toner_level: data.toner_level,
        paper_level: data.paper_level,
        timestamp: data.timestamp || new Date().toISOString(),
      });
      if (data.response_time_ms !== undefined) {
        setLatency(data.response_time_ms);
      }
    },
    [id, updateStatus]
  );

  const { connected } = useWebSocket({
    deviceId: id || null,
    onMessage: handleWsMessage,
  });

  // Fetch device detail
  useEffect(() => {
    if (id) {
      fetchDevice(id);
    }
  }, [id, fetchDevice]);

  const fetchLogs = useCallback(async () => {
    if (!id) return;
    setLoadingLogs(true);
    try {
      const data = await devicesApi.getLogs(id, { hours: 24, limit: 100 });
      setLogs(data);
    } catch {
      setLogs([]);
    } finally {
      setLoadingLogs(false);
    }
  }, [id]);

  const fetchAlerts = useCallback(async () => {
    if (!id) return;
    setLoadingAlerts(true);
    try {
      const data = await devicesApi.getAlerts(id);
      setAlerts(data);
    } catch {
      setAlerts([]);
    } finally {
      setLoadingAlerts(false);
    }
  }, [id]);

  const fetchQueue = useCallback(async () => {
    if (!id) return;
    setLoadingQueue(true);
    try {
      const data = await devicesApi.getQueue(id);
      setQueue(Array.isArray(data) ? data : []);
    } catch {
      setQueue([]);
    } finally {
      setLoadingQueue(false);
    }
  }, [id]);

  useEffect(() => {
    fetchLogs();
    fetchAlerts();
    fetchQueue();
  }, [fetchLogs, fetchAlerts, fetchQueue]);

  const handleRefreshAll = useCallback(() => {
    if (!id) return;
    fetchDevice(id);
    fetchLogs();
    fetchAlerts();
    fetchQueue();
  }, [id, fetchDevice, fetchLogs, fetchAlerts, fetchQueue]);

  const handleResolveAlert = useCallback(
    async (alertId: string) => {
      if (!id) return;
      try {
        await devicesApi.resolveAlert(id, alertId);
        message.success('告警已解决');
        fetchAlerts();
      } catch {
        message.error('操作失败');
      }
    },
    [id, fetchAlerts]
  );

  const handleResolveAllAlerts = useCallback(() => {
    const unresolved = alerts.filter((a) => !a.is_resolved);
    if (unresolved.length === 0) {
      message.info('没有未解决的告警');
      return;
    }
    Promise.all(unresolved.map((a) => handleResolveAlert(a.id)));
  }, [alerts, handleResolveAlert]);

  // ECharts option for status history (toner/paper levels over time)
  const historyChartOption = useMemo(() => {
    const sortedLogs = [...logs].sort(
      (a, b) =>
        dayjs(a.recorded_at).valueOf() - dayjs(b.recorded_at).valueOf()
    );
    const times = sortedLogs.map((l) =>
      dayjs(l.recorded_at).format('HH:mm')
    );
    const tonerData = sortedLogs.map((l) => l.toner_level ?? 0);
    const paperData = sortedLogs.map((l) => l.paper_level ?? 0);

    return {
      tooltip: {
        trigger: 'axis' as const,
        formatter: (params: { seriesName: string; value: number; axisValue: string }[]) => {
          let result = `${params[0].axisValue}<br/>`;
          params.forEach((p) => {
            result += `${p.seriesName}: ${p.value}%<br/>`;
          });
          return result;
        },
      },
      legend: {
        data: ['墨粉余量', '纸张余量'],
        bottom: 0,
      },
      grid: { left: '3%', right: '4%', bottom: '12%', top: '8%', containLabel: true },
      xAxis: {
        type: 'category' as const,
        data: times,
        boundaryGap: false,
      },
      yAxis: {
        type: 'value' as const,
        max: 100,
        axisLabel: { formatter: '{value}%' },
      },
      series: [
        {
          name: '墨粉余量',
          type: 'line',
          data: tonerData,
          smooth: true,
          symbol: 'circle',
          symbolSize: 4,
          lineStyle: { color: '#1677ff', width: 2 },
          itemStyle: { color: '#1677ff' },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(22,119,255,0.25)' },
                { offset: 1, color: 'rgba(22,119,255,0.02)' },
              ],
            },
          },
        },
        {
          name: '纸张余量',
          type: 'line',
          data: paperData,
          smooth: true,
          symbol: 'circle',
          symbolSize: 4,
          lineStyle: { color: '#52c41a', width: 2 },
          itemStyle: { color: '#52c41a' },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(82,196,26,0.25)' },
                { offset: 1, color: 'rgba(82,196,26,0.02)' },
              ],
            },
          },
        },
      ],
    };
  }, [logs]);

  // Alert table columns
  const alertColumns = useMemo(
    () => [
      {
        title: '时间',
        dataIndex: 'created_at',
        key: 'created_at',
        width: 160,
        render: (v: string) => dayjs(v).format('MM-DD HH:mm:ss'),
      },
      {
        title: '告警类型',
        dataIndex: 'alert_type',
        key: 'alert_type',
        width: 120,
        render: (v: string) => alertTypeLabels[v] || v,
      },
      {
        title: '严重程度',
        dataIndex: 'severity',
        key: 'severity',
        width: 100,
        render: (v: AlertSeverity) => (
          <Tag color={severityColorMap[v]}>{severityLabelMap[v]}</Tag>
        ),
      },
      {
        title: '消息',
        dataIndex: 'message',
        key: 'message',
        ellipsis: true,
      },
      {
        title: '状态',
        dataIndex: 'is_resolved',
        key: 'is_resolved',
        width: 90,
        render: (v: boolean) => (
          <Tag color={v ? 'default' : 'error'}>
            {v ? '已解决' : '未解决'}
          </Tag>
        ),
      },
      {
        title: '操作',
        key: 'actions',
        width: 80,
        render: (_: unknown, record: PrinterAlert) =>
          !record.is_resolved ? (
            <Button
              type="link"
              size="small"
              onClick={() => handleResolveAlert(record.id)}
            >
              解决
            </Button>
          ) : null,
      },
    ],
    [handleResolveAlert]
  );

  // Queue table columns
  const queueColumns = useMemo(
    () => [
      {
        title: '文件名',
        dataIndex: 'document_name',
        key: 'document_name',
      },
      {
        title: '页数',
        dataIndex: 'pages',
        key: 'pages',
        width: 80,
      },
      {
        title: '份数',
        dataIndex: 'copies',
        key: 'copies',
        width: 80,
      },
      {
        title: '状态',
        dataIndex: 'status',
        key: 'status',
        width: 100,
        render: (v: string) => {
          const info = queueStatusMap[v] || { color: 'default', text: v };
          return <Tag color={info.color}>{info.text}</Tag>;
        },
      },
      {
        title: '提交时间',
        dataIndex: 'created_at',
        key: 'created_at',
        width: 140,
        render: (v: string) => (v ? dayjs(v).format('HH:mm:ss') : '-'),
      },
    ],
    []
  );

  const tabItems = useMemo(
    () => [
      {
        key: 'history',
        label: '状态历史',
        children: (
          <div style={{ minHeight: 350 }}>
            {logs.length === 0 ? (
              <div
                style={{
                  height: 350,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#999',
                }}
              >
                暂无历史数据
              </div>
            ) : (
              <ReactECharts
                option={historyChartOption}
                style={{ height: 350 }}
              />
            )}
          </div>
        ),
      },
      {
        key: 'alerts',
        label: `告警记录 (${alerts.length})`,
        children: (
          <Table
            columns={alertColumns}
            dataSource={alerts}
            rowKey="id"
            loading={loadingAlerts}
            pagination={{ pageSize: 10, showSizeChanger: true }}
            size="small"
          />
        ),
      },
      {
        key: 'queue',
        label: '打印队列',
        children: (
          <Table
            columns={queueColumns}
            dataSource={queue}
            rowKey="id"
            loading={loadingQueue}
            pagination={{ pageSize: 10, showSizeChanger: true }}
            size="small"
          />
        ),
      },
    ],
    [
      logs,
      historyChartOption,
      alerts,
      alertColumns,
      loadingAlerts,
      queue,
      queueColumns,
      loadingQueue,
    ]
  );

  // Loading state
  if (!selectedDevice) {
    return (
      <div
        className="page-container"
        style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '60vh',
        }}
      >
        <Spin size="large" tip="加载设备信息..." />
      </div>
    );
  }

  const device = selectedDevice;

  return (
    <div className="page-container">
      {/* Breadcrumb + Actions */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 16,
          flexWrap: 'wrap',
          gap: 8,
        }}
      >
        <Breadcrumb
          items={[
            {
              title: (
                <>
                  <HomeOutlined /> 首页
                </>
              ),
              onClick: () => navigate('/dashboard'),
            },
            {
              title: '设备管理',
              onClick: () => navigate('/devices'),
            },
            { title: device.name },
          ]}
        />
        <Space>
          <Button
            icon={<ReloadOutlined />}
            onClick={handleRefreshAll}
          >
            刷新
          </Button>
          <Button
            icon={<CheckCircleOutlined />}
            onClick={handleResolveAllAlerts}
          >
            解决全部告警
          </Button>
        </Space>
      </div>

      {/* Row 1: Info + Real-time Status */}
      <Row gutter={[16, 16]}>
        <Col span={16}>
          <Card title="设备信息">
            <Descriptions column={2} size="small" bordered>
              <Descriptions.Item label="设备名称">
                {device.name}
              </Descriptions.Item>
              <Descriptions.Item label="品牌">
                {device.brand}
              </Descriptions.Item>
              <Descriptions.Item label="型号">
                {device.model}
              </Descriptions.Item>
              <Descriptions.Item label="序列号">
                {device.serial_number || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="IP 地址">
                {device.ip_address}
              </Descriptions.Item>
              <Descriptions.Item label="MAC 地址">
                {device.mac_address || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="位置">
                {device.location || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="状态">
                <StatusBadge status={device.status} />
              </Descriptions.Item>
              <Descriptions.Item label="固件版本">
                {device.firmware_version || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="总印量">
                {device.total_pages_printed.toLocaleString()} 页
              </Descriptions.Item>
            </Descriptions>
          </Card>
        </Col>

        <Col span={8}>
          <Card title="实时状态">
            {/* Large status display with pulse */}
            <div style={{ textAlign: 'center', marginBottom: 20 }}>
              <div
                style={{
                  position: 'relative',
                  display: 'inline-flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  width: 80,
                  height: 80,
                  borderRadius: '50%',
                  background:
                    device.status === 'online'
                      ? 'rgba(82,196,26,0.1)'
                      : device.status === 'error'
                        ? 'rgba(255,77,79,0.1)'
                        : device.status === 'busy'
                          ? 'rgba(250,140,22,0.1)'
                          : 'rgba(140,140,140,0.1)',
                }}
              >
                <span
                  style={{
                    display: 'inline-block',
                    width: 24,
                    height: 24,
                    borderRadius: '50%',
                    backgroundColor:
                      device.status === 'online'
                        ? '#52c41a'
                        : device.status === 'error'
                          ? '#ff4d4f'
                          : device.status === 'busy'
                            ? '#fa8c16'
                            : '#8c8c8c',
                    animation:
                      device.status === 'online'
                        ? 'pulse 1.5s ease-in-out infinite'
                        : 'none',
                  }}
                />
                {device.status === 'online' && (
                  <>
                    <span
                      style={{
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        width: '100%',
                        height: '100%',
                        borderRadius: '50%',
                        backgroundColor: 'rgba(82,196,26,0.2)',
                        animation: 'pulse-ring 1.5s ease-out infinite',
                      }}
                    />
                    <style>{`
                      @keyframes pulse {
                        0%, 100% { transform: scale(1); }
                        50% { transform: scale(1.15); }
                      }
                      @keyframes pulse-ring {
                        0% { transform: scale(1); opacity: 0.6; }
                        100% { transform: scale(1.8); opacity: 0; }
                      }
                    `}</style>
                  </>
                )}
              </div>
              <div style={{ marginTop: 12 }}>
                <Text strong style={{ fontSize: 18 }}>
                  <StatusBadge status={device.status} />
                </Text>
              </div>
              {connected && (
                <Tag color="green" style={{ marginTop: 8 }}>
                  <WifiOutlined /> 实时连接
                </Tag>
              )}
              {!connected && id && (
                <Tag color="default" style={{ marginTop: 8 }}>
                  连接断开
                </Tag>
              )}
            </div>

            {/* Toner level */}
            <div style={{ textAlign: 'center', marginBottom: 20 }}>
              <Text type="secondary">墨粉余量</Text>
              <div style={{ marginTop: 8 }}>
                <Progress
                  type="circle"
                  percent={device.toner_level}
                  size={100}
                  strokeColor={
                    device.toner_level < 20
                      ? '#ff4d4f'
                      : device.toner_level < 50
                        ? '#faad14'
                        : '#1677ff'
                  }
                  format={(pct) => `${pct}%`}
                />
              </div>
            </div>

            {/* Paper level */}
            <div style={{ textAlign: 'center', marginBottom: 20 }}>
              <Text type="secondary">纸张余量</Text>
              <div style={{ marginTop: 8 }}>
                <Progress
                  type="circle"
                  percent={device.paper_level}
                  size={100}
                  strokeColor={
                    device.paper_level < 20
                      ? '#ff4d4f'
                      : device.paper_level < 50
                        ? '#faad14'
                        : '#52c41a'
                  }
                  format={(pct) => `${pct}%`}
                />
              </div>
            </div>

            {/* Latency */}
            {latency !== null && (
              <div style={{ marginBottom: 12 }}>
                <Text type="secondary" style={{ display: 'block', textAlign: 'center' }}>
                  <ClockCircleOutlined /> 连接延迟
                </Text>
                <div style={{ textAlign: 'center', marginTop: 4 }}>
                  <Text strong style={{ fontSize: 16 }}>
                    {latency} ms
                  </Text>
                </div>
              </div>
            )}

            {/* Last seen */}
            {device.last_seen_at && (
              <div style={{ textAlign: 'center' }}>
                <Text type="secondary">
                  最后在线: {dayjs(device.last_seen_at).format('MM-DD HH:mm:ss')}
                </Text>
              </div>
            )}
          </Card>
        </Col>
      </Row>

      {/* Row 2: Tabs */}
      <Row style={{ marginTop: 16 }}>
        <Col span={24}>
          <Card>
            <Tabs defaultActiveKey="history" items={tabItems} />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default DeviceDetailPage;
