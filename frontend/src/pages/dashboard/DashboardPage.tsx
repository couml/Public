import React, { useEffect, useMemo } from 'react';
import { Row, Col, Table, Tag } from 'antd';
import {
  PrinterOutlined,
  CheckCircleOutlined,
  AlertOutlined,
  FileTextOutlined,
} from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import dayjs from 'dayjs';
import StatCard from '@/components/StatCard';
import StatusBadge from '@/components/StatusBadge';
import { useDeviceStore } from '@/store/deviceStore';
import type { PrinterAlert, AlertSeverity } from '@/types/device';

const severityColorMap: Record<AlertSeverity, string> = {
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

function generateMockAlerts(
  devices: import('@/types/device').Printer[]
): (PrinterAlert & { printer_name: string })[] {
  const existingIds = new Set<string>();
  const alerts: (PrinterAlert & { printer_name: string })[] = [];

  devices.forEach((device) => {
    if (device.status === 'error') {
      const id = `alert-err-${device.id}`;
      existingIds.add(id);
      alerts.push({
        id,
        printer_id: device.id,
        printer_name: device.name,
        alert_type: 'service_required',
        severity: 'critical',
        message: `设备 ${device.name} 报告故障状态`,
        is_resolved: false,
        resolved_by: null,
        resolved_at: null,
        created_at: dayjs()
          .subtract(Math.floor(Math.random() * 60), 'minute')
          .toISOString(),
      });
    }
    if (device.toner_level <= 10 && device.toner_level > 0) {
      const id = `alert-toner-${device.id}`;
      existingIds.add(id);
      alerts.push({
        id,
        printer_id: device.id,
        printer_name: device.name,
        alert_type: 'toner_low',
        severity: 'warning',
        message: `设备 ${device.name} 墨粉不足 (${device.toner_level}%)`,
        is_resolved: false,
        resolved_by: null,
        resolved_at: null,
        created_at: dayjs()
          .subtract(Math.floor(Math.random() * 120), 'minute')
          .toISOString(),
      });
    }
    if (device.toner_level === 0) {
      const id = `alert-toner-empty-${device.id}`;
      existingIds.add(id);
      alerts.push({
        id,
        printer_id: device.id,
        printer_name: device.name,
        alert_type: 'toner_empty',
        severity: 'critical',
        message: `设备 ${device.name} 墨粉已耗尽`,
        is_resolved: false,
        resolved_by: null,
        resolved_at: null,
        created_at: dayjs()
          .subtract(Math.floor(Math.random() * 30), 'minute')
          .toISOString(),
      });
    }
    if (device.status === 'offline') {
      const id = `alert-off-${device.id}`;
      existingIds.add(id);
      alerts.push({
        id,
        printer_id: device.id,
        printer_name: device.name,
        alert_type: 'offline',
        severity: 'warning',
        message: `设备 ${device.name} 已离线`,
        is_resolved: false,
        resolved_by: null,
        resolved_at: null,
        created_at: dayjs()
          .subtract(Math.floor(Math.random() * 30), 'minute')
          .toISOString(),
      });
    }
  });

  return alerts.sort(
    (a, b) => dayjs(b.created_at).valueOf() - dayjs(a.created_at).valueOf()
  );
}

const DashboardPage: React.FC = () => {
  const { devices, isLoading, fetchDevices } = useDeviceStore();

  useEffect(() => {
    fetchDevices();
  }, [fetchDevices]);

  const stats = useMemo(() => {
    const online = devices.filter((d) => d.status === 'online').length;
    const activeAlerts = devices.filter(
      (d) => d.status === 'error' || d.status === 'offline' || d.toner_level <= 10
    ).length;
    return {
      total: devices.length,
      online,
      alerts: activeAlerts,
      todayJobs: Math.floor(Math.random() * 200) + 50,
    };
  }, [devices]);

  const alerts = useMemo(() => generateMockAlerts(devices), [devices]);

  const pieOption = useMemo(() => {
    const statusCount: Record<string, number> = {
      online: 0,
      offline: 0,
      busy: 0,
      error: 0,
    };
    devices.forEach((d) => {
      statusCount[d.status] = (statusCount[d.status] || 0) + 1;
    });
    return {
      tooltip: { trigger: 'item' as const },
      legend: { bottom: 0 },
      series: [
        {
          name: '设备状态',
          type: 'pie' as const,
          radius: ['40%', '70%'],
          center: ['50%', '45%'],
          avoidLabelOverlap: false,
          itemStyle: { borderRadius: 4, borderColor: '#fff', borderWidth: 2 },
          label: { show: true, formatter: '{b}: {c}' },
          data: [
            { value: statusCount.online, name: '在线', itemStyle: { color: '#52c41a' } },
            { value: statusCount.offline, name: '离线', itemStyle: { color: '#8c8c8c' } },
            { value: statusCount.busy, name: '繁忙', itemStyle: { color: '#fa8c16' } },
            { value: statusCount.error, name: '故障', itemStyle: { color: '#ff4d4f' } },
          ],
        },
      ],
    };
  }, [devices]);

  const barOption = useMemo(() => {
    const sorted = [...devices]
      .sort((a, b) => b.toner_level - a.toner_level)
      .slice(0, 10);
    const reversed = [...sorted].reverse();
    return {
      tooltip: {
        trigger: 'axis' as const,
        axisPointer: { type: 'shadow' as const },
      },
      grid: { left: '3%', right: '8%', bottom: '3%', containLabel: true },
      xAxis: {
        type: 'value' as const,
        max: 100,
        axisLabel: { formatter: '{value}%' },
      },
      yAxis: {
        type: 'category' as const,
        data: reversed.map((d) => d.name),
        axisLabel: {
          width: 100,
          overflow: 'truncate',
          ellipsis: '...',
        },
      },
      series: [
        {
          name: '墨粉余量',
          type: 'bar' as const,
          data: reversed.map((d) => ({
            value: d.toner_level,
            itemStyle: {
              color:
                d.toner_level < 20
                  ? '#ff4d4f'
                  : d.toner_level < 50
                    ? '#faad14'
                    : '#52c41a',
            },
          })),
          label: {
            show: true,
            position: 'right' as const,
            formatter: '{c}%',
          },
        },
      ],
    };
  }, [devices]);

  const alertColumns = [
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (v: string) => dayjs(v).format('MM-DD HH:mm:ss'),
    },
    {
      title: '打印机',
      dataIndex: 'printer_name',
      key: 'printer_name',
    },
    {
      title: '告警类型',
      dataIndex: 'alert_type',
      key: 'alert_type',
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
      title: '状态',
      dataIndex: 'is_resolved',
      key: 'is_resolved',
      width: 100,
      render: (v: boolean) => (
        <Tag color={v ? 'default' : 'error'}>{v ? '已解决' : '未解决'}</Tag>
      ),
    },
  ];

  return (
    <div className="page-container">
      <Row gutter={[16, 16]}>
        <Col span={6}>
          <StatCard
            title="设备总数"
            value={stats.total}
            icon={<PrinterOutlined />}
            color="#1677ff"
            loading={isLoading}
          />
        </Col>
        <Col span={6}>
          <StatCard
            title="在线设备"
            value={stats.online}
            icon={<CheckCircleOutlined />}
            color="#52c41a"
            loading={isLoading}
          />
        </Col>
        <Col span={6}>
          <StatCard
            title="活跃告警"
            value={stats.alerts}
            icon={<AlertOutlined />}
            color="#faad14"
            loading={isLoading}
          />
        </Col>
        <Col span={6}>
          <StatCard
            title="今日打印"
            value={stats.todayJobs}
            icon={<FileTextOutlined />}
            color="#722ed1"
            loading={isLoading}
          />
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={12}>
          <div
            style={{
              background: '#fff',
              borderRadius: 6,
              padding: 16,
              height: '100%',
            }}
          >
            <h3 style={{ marginBottom: 16 }}>设备状态分布</h3>
            <ReactECharts option={pieOption} style={{ height: 300 }} />
          </div>
        </Col>
        <Col span={12}>
          <div
            style={{
              background: '#fff',
              borderRadius: 6,
              padding: 16,
              height: '100%',
            }}
          >
            <h3 style={{ marginBottom: 16 }}>墨粉余量 Top 10</h3>
            {devices.length === 0 ? (
              <div
                style={{
                  height: 300,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#999',
                }}
              >
                暂无数据
              </div>
            ) : (
              <ReactECharts option={barOption} style={{ height: 300 }} />
            )}
          </div>
        </Col>
      </Row>

      <div
        style={{
          marginTop: 16,
          background: '#fff',
          borderRadius: 6,
          padding: 16,
        }}
      >
        <h3 style={{ marginBottom: 16 }}>最近告警</h3>
        <Table
          columns={alertColumns}
          dataSource={alerts}
          rowKey="id"
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条`,
          }}
          size="small"
        />
      </div>
    </div>
  );
};

export default DashboardPage;
