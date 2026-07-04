import React, { useState, useEffect, useCallback } from 'react';
import { Card, Table, Tag, Button, Space, Select, DatePicker, Row, Col, message } from 'antd';
import { ReloadOutlined, EyeOutlined, PrinterOutlined, FileTextOutlined, CheckCircleOutlined, CloseCircleOutlined, CopyOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import PageHeader from '@/components/PageHeader';
import StatCard from '@/components/StatCard';
import PrinterSelector from '@/components/PrinterSelector';
import { printApi } from '@/api/print';
import { formatFileSize } from '@/utils/format';
import type { PrintJob, PrintJobStats } from '@/types/print';
import dayjs from 'dayjs';

const { RangePicker } = DatePicker;

const STATUS_TAG: Record<string, { color: string; label: string }> = {
  queued: { color: 'blue', label: '排队中' },
  converting: { color: 'purple', label: '转换中' },
  waiting: { color: 'orange', label: '等待中' },
  printing: { color: 'processing', label: '打印中' },
  completed: { color: 'green', label: '已完成' },
  failed: { color: 'red', label: '失败' },
  cancelled: { color: 'default', label: '已取消' },
};

const STATUS_OPTIONS = [
  { label: '全部状态', value: '' },
  { label: '排队中', value: 'queued' },
  { label: '打印中', value: 'printing' },
  { label: '已完成', value: 'completed' },
  { label: '失败', value: 'failed' },
  { label: '已取消', value: 'cancelled' },
];

const PrintHistoryPage: React.FC = () => {
  // ---------- Filters ----------
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [printerFilter, setPrinterFilter] = useState<string | undefined>();

  // ---------- Data ----------
  const [jobs, setJobs] = useState<PrintJob[]>([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [total, setTotal] = useState(0);

  // ---------- Stats ----------
  const [stats, setStats] = useState<PrintJobStats | null>(null);
  const [statsLoading, setStatsLoading] = useState(false);

  const fetchJobs = useCallback(async () => {
    setLoading(true);
    try {
      const params: { status?: string; page: number; page_size: number } = {
        page,
        page_size: pageSize,
      };
      if (statusFilter) params.status = statusFilter;
      const res = await printApi.list(params);
      setJobs(res.items);
      setTotal(res.total);
    } catch {
      message.error('获取打印记录失败');
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, statusFilter]);

  const fetchStats = useCallback(async () => {
    setStatsLoading(true);
    try {
      const data = await printApi.getStats();
      setStats(data);
    } catch {
      // silent
    } finally {
      setStatsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchJobs();
  }, [fetchJobs]);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  const handleRefresh = () => {
    fetchJobs();
    fetchStats();
  };

  const handleReprint = async (job: PrintJob) => {
    try {
      await printApi.submitJob({
        printer_id: job.printer_id,
        file_id: job.file_id,
        copies: job.copies,
        color_mode: job.color_mode,
        duplex: job.duplex,
        paper_size: job.paper_size,
        page_range: job.page_range ?? undefined,
        n_up: job.n_up,
        orientation: job.orientation,
      });
      message.success('已重新提交打印任务');
      fetchJobs();
    } catch {
      message.error('重新打印失败');
    }
  };

  // ---------- Table columns ----------

  const columns: ColumnsType<PrintJob> = [
    {
      title: '任务名称',
      dataIndex: 'job_name',
      key: 'job_name',
      width: 160,
      ellipsis: true,
      render: (name: string | null, record) => name || record.id.slice(0, 8),
    },
    {
      title: '打印机',
      dataIndex: 'printer_id',
      key: 'printer_id',
      width: 140,
      ellipsis: true,
      render: (id: string) => <Tag>{id.slice(0, 12)}</Tag>,
    },
    {
      title: '文件',
      dataIndex: 'file_id',
      key: 'file_id',
      width: 140,
      ellipsis: true,
      render: (id: string) => <span style={{ fontSize: 12, color: '#8c8c8c' }}>{id.slice(0, 12)}</span>,
    },
    {
      title: '页数',
      dataIndex: 'total_pages',
      key: 'total_pages',
      width: 80,
      align: 'center',
      render: (pages: number | null) => pages ?? '-',
    },
    {
      title: '份数',
      dataIndex: 'copies',
      key: 'copies',
      width: 70,
      align: 'center',
    },
    {
      title: '色彩',
      dataIndex: 'color_mode',
      key: 'color_mode',
      width: 70,
      align: 'center',
      render: (mode: string) => (mode === 'color' ? '彩色' : '黑白'),
    },
    {
      title: '双面',
      dataIndex: 'duplex',
      key: 'duplex',
      width: 70,
      align: 'center',
      render: (v: boolean) => (v ? <Tag color="blue">是</Tag> : <Tag>否</Tag>),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      align: 'center',
      render: (status: string) => {
        const cfg = STATUS_TAG[status] || { color: 'default', label: status };
        return <Tag color={cfg.color}>{cfg.label}</Tag>;
      },
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '操作',
      key: 'actions',
      width: 120,
      render: (_, record) => (
        <Space size="small">
          <Button type="link" size="small" icon={<EyeOutlined />}>
            详情
          </Button>
          <Button
            type="link"
            size="small"
            icon={<ReloadOutlined />}
            onClick={() => handleReprint(record)}
          >
            重打
          </Button>
        </Space>
      ),
    },
  ];

  // ---------- Render ----------

  return (
    <div style={{ padding: 24 }}>
      <PageHeader
        title="打印历史记录"
        extra={
          <Button icon={<ReloadOutlined />} onClick={handleRefresh}>
            刷新
          </Button>
        }
      />

      {/* Stats Row */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={12} sm={6}>
          <StatCard
            title="总任务数"
            value={stats?.total_jobs ?? '-'}
            icon={<FileTextOutlined />}
            color="#1677ff"
            loading={statsLoading}
          />
        </Col>
        <Col xs={12} sm={6}>
          <StatCard
            title="今日完成"
            value={stats?.completed_today ?? '-'}
            icon={<CheckCircleOutlined />}
            color="#52c41a"
            loading={statsLoading}
          />
        </Col>
        <Col xs={12} sm={6}>
          <StatCard
            title="今日失败"
            value={stats?.failed_today ?? '-'}
            icon={<CloseCircleOutlined />}
            color="#ff4d4f"
            loading={statsLoading}
          />
        </Col>
        <Col xs={12} sm={6}>
          <StatCard
            title="今日页数"
            value={stats?.total_pages_today ?? '-'}
            icon={<CopyOutlined />}
            color="#722ed1"
            loading={statsLoading}
          />
        </Col>
      </Row>

      {/* Filter Bar */}
      <Card style={{ marginBottom: 24 }}>
        <Space wrap size="middle">
          <span style={{ color: '#8c8c8c' }}>时间范围：</span>
          <RangePicker
            value={dateRange}
            onChange={(dates) => setDateRange(dates as [dayjs.Dayjs, dayjs.Dayjs] | null)}
            allowClear
          />
          <span style={{ color: '#8c8c8c' }}>状态：</span>
          <Select
            value={statusFilter}
            onChange={(v) => {
              setStatusFilter(v);
              setPage(1);
            }}
            options={STATUS_OPTIONS}
            style={{ width: 130 }}
          />
          <span style={{ color: '#8c8c8c' }}>打印机：</span>
          <PrinterSelector value={printerFilter} onChange={setPrinterFilter} />
        </Space>
      </Card>

      {/* Jobs Table */}
      <Card>
        <Table
          rowKey="id"
          columns={columns}
          dataSource={jobs}
          loading={loading}
          pagination={{
            current: page,
            pageSize,
            total,
            showSizeChanger: true,
            showTotal: (t) => `共 ${t} 条记录`,
            onChange: (p, ps) => {
              setPage(p);
              setPageSize(ps);
            },
          }}
          scroll={{ x: 1300 }}
          locale={{ emptyText: '暂无打印记录' }}
        />
      </Card>
    </div>
  );
};

export default PrintHistoryPage;
