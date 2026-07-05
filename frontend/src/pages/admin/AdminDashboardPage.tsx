import React, { useEffect, useState } from 'react';
import { Row, Col, Card, Table, Typography, Spin, Alert } from 'antd';
import {
  TeamOutlined,
  PrinterOutlined,
  FileTextOutlined,
  AlertOutlined,
} from '@ant-design/icons';
import ReactEChartsCore from 'echarts-for-react/lib/core';
import * as echarts from 'echarts/core';
import { PieChart } from 'echarts/charts';
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
} from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import PageHeader from '@/components/PageHeader';
import StatCard from '@/components/StatCard';
import { adminApi } from '@/api/admin';
import { formatDate } from '@/utils/format';

echarts.use([PieChart, TitleComponent, TooltipComponent, LegendComponent, CanvasRenderer]);

const { Text } = Typography;

interface DashboardStats {
  total_users: number;
  total_printers: number;
  today_print_jobs: number;
  active_alerts: number;
  device_status_distribution: { status: string; count: number }[];
  recent_activities: ActivityLog[];
}

interface ActivityLog {
  id: string;
  time: string;
  user: string;
  action: string;
  resource: string;
  detail: string;
}

const statusLabelMap: Record<string, string> = {
  online: '在线',
  offline: '离线',
  busy: '繁忙',
  error: '故障',
};

const statusColorMap: Record<string, string> = {
  online: '#52c41a',
  offline: '#8c8c8c',
  busy: '#1677ff',
  error: '#ff4d4f',
};

const AdminDashboardPage: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await adminApi.getStats();
      setStats(data as DashboardStats);
    } catch (err: any) {
      setError(err?.response?.data?.message || '获取统计数据失败');
    } finally {
      setLoading(false);
    }
  };

  const activityColumns = [
    { title: '时间', dataIndex: 'time', key: 'time', width: 160, render: (v: string) => formatDate(v) },
    { title: '用户', dataIndex: 'user', key: 'user', width: 100 },
    { title: '操作', dataIndex: 'action', key: 'action', width: 100 },
    { title: '资源', dataIndex: 'resource', key: 'resource', width: 120 },
    { title: '详情', dataIndex: 'detail', key: 'detail', ellipsis: true },
  ];

  const pieOption = stats?.device_status_distribution
    ? {
        tooltip: { trigger: 'item' as const },
        legend: { bottom: 0 },
        series: [
          {
            name: '设备状态',
            type: 'pie' as const,
            radius: ['45%', '70%'],
            avoidLabelOverlap: false,
            itemStyle: { borderRadius: 4, borderColor: '#fff', borderWidth: 2 },
            label: { show: false },
            emphasis: { label: { show: true, fontSize: 14, fontWeight: 'bold' } },
            data: stats.device_status_distribution.map((d) => ({
              name: statusLabelMap[d.status] || d.status,
              value: d.count,
              itemStyle: { color: statusColorMap[d.status] || '#d9d9d9' },
            })),
          },
        ],
      }
    : null;

  return (
    <>
      <PageHeader title="管理后台" />
      {error && <Alert message={error} type="error" showIcon style={{ marginBottom: 16 }} closable onClose={() => setError(null)} />}
      <Spin spinning={loading}>
        {/* Stat Cards */}
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col xs={12} sm={12} md={6}>
            <StatCard
              title="用户总数"
              value={stats?.total_users ?? '-'}
              icon={<TeamOutlined />}
              color="#1677ff"
              loading={loading}
            />
          </Col>
          <Col xs={12} sm={12} md={6}>
            <StatCard
              title="设备总数"
              value={stats?.total_printers ?? '-'}
              icon={<PrinterOutlined />}
              color="#52c41a"
              loading={loading}
            />
          </Col>
          <Col xs={12} sm={12} md={6}>
            <StatCard
              title="今日打印任务"
              value={stats?.today_print_jobs ?? '-'}
              icon={<FileTextOutlined />}
              color="#faad14"
              loading={loading}
            />
          </Col>
          <Col xs={12} sm={12} md={6}>
            <StatCard
              title="活跃告警"
              value={stats?.active_alerts ?? '-'}
              icon={<AlertOutlined />}
              color="#ff4d4f"
              loading={loading}
            />
          </Col>
        </Row>

        <Row gutter={[16, 16]}>
          {/* Recent Activity Table */}
          <Col xs={24} lg={16}>
            <Card title="最近活动" styles={{ body: { padding: 0 } }}>
              <Table<ActivityLog>
                columns={activityColumns}
                dataSource={stats?.recent_activities || []}
                rowKey="id"
                pagination={false}
                size="small"
                scroll={{ x: 600 }}
              />
            </Card>
          </Col>

          {/* Device Status Distribution */}
          <Col xs={24} lg={8}>
            <Card title="设备状态分布">
              {pieOption ? (
                <ReactEChartsCore echarts={echarts} option={pieOption} style={{ height: 280 }} />
              ) : (
                <div style={{ height: 280, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Text type="secondary">暂无数据</Text>
                </div>
              )}
            </Card>
          </Col>
        </Row>
      </Spin>
    </>
  );
};

export default AdminDashboardPage;
