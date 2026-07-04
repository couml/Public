import React, { useEffect, useState, useCallback, useRef } from 'react';
import {
  Table,
  Card,
  Select,
  DatePicker,
  Input,
  Space,
  Tag,
  Button,
  Switch,
  Typography,
  message,
} from 'antd';
import { ReloadOutlined, SearchOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';
import PageHeader from '@/components/PageHeader';
import { adminApi } from '@/api/admin';
import { formatDate } from '@/utils/format';
import { usePagination } from '@/hooks/usePagination';
import type { PaginatedResponse } from '@/types/api';

const { RangePicker } = DatePicker;
const { Text } = Typography;

interface LogEntry {
  id: string;
  time: string;
  user: string;
  action: string;
  resource: string;
  resource_id: string;
  ip_address: string;
  detail: Record<string, unknown> | string;
}

const actionOptions = [
  { label: '登录', value: 'login' },
  { label: '登出', value: 'logout' },
  { label: '创建', value: 'create' },
  { label: '更新', value: 'update' },
  { label: '删除', value: 'delete' },
  { label: '打印', value: 'print' },
  { label: '上传', value: 'upload' },
  { label: '下载', value: 'download' },
  { label: '配置修改', value: 'config_change' },
];

const actionColorMap: Record<string, string> = {
  login: 'green',
  logout: 'default',
  create: 'blue',
  update: 'orange',
  delete: 'red',
  print: 'purple',
  upload: 'cyan',
  download: 'geekblue',
  config_change: 'volcano',
};

const AdminLogPage: React.FC = () => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [filterAction, setFilterAction] = useState<string | undefined>(undefined);
  const [filterUser, setFilterUser] = useState('');
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const { page, pageSize, onChange, reset } = usePagination(20);

  const fetchLogs = useCallback(async () => {
    setLoading(true);
    try {
      const params: any = { page, page_size: pageSize };
      if (filterAction) params.action = filterAction;
      if (filterUser) params.user_id = filterUser;
      if (dateRange) {
        params.start_time = dateRange[0].startOf('day').toISOString();
        params.end_time = dateRange[1].endOf('day').toISOString();
      }
      const data: PaginatedResponse<LogEntry> = await adminApi.getLogs(params);
      setLogs(data.items);
      setTotal(data.total);
    } catch (err: any) {
      message.error(err?.response?.data?.message || '获取日志失败');
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, filterAction, filterUser, dateRange]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  // Auto-refresh
  useEffect(() => {
    if (autoRefresh) {
      timerRef.current = setInterval(fetchLogs, 30000);
    } else {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    };
  }, [autoRefresh, fetchLogs]);

  const handleFilter = () => {
    reset();
  };

  const formatDetail = (detail: Record<string, unknown> | string): string => {
    if (typeof detail === 'string') return detail;
    try {
      return JSON.stringify(detail, null, 2);
    } catch {
      return String(detail);
    }
  };

  const columns: ColumnsType<LogEntry> = [
    {
      title: '时间',
      dataIndex: 'time',
      key: 'time',
      width: 160,
      render: (v: string) => formatDate(v),
      sorter: (a, b) => new Date(a.time).getTime() - new Date(b.time).getTime(),
      defaultSortOrder: 'descend',
    },
    { title: '用户', dataIndex: 'user', key: 'user', width: 110 },
    {
      title: '操作',
      dataIndex: 'action',
      key: 'action',
      width: 100,
      render: (action: string) => {
        const opt = actionOptions.find((a) => a.value === action);
        return (
          <Tag color={actionColorMap[action] || 'default'}>
            {opt?.label || action}
          </Tag>
        );
      },
    },
    { title: '资源', dataIndex: 'resource', key: 'resource', width: 110 },
    {
      title: '资源 ID',
      dataIndex: 'resource_id',
      key: 'resource_id',
      width: 180,
      ellipsis: true,
      render: (v: string) => v || '-',
    },
    {
      title: 'IP 地址',
      dataIndex: 'ip_address',
      key: 'ip_address',
      width: 130,
      render: (v: string) => v || '-',
    },
  ];

  return (
    <>
      <PageHeader
        title="系统日志"
        extra={
          <Space>
            <Space size={4}>
              <Text type="secondary" style={{ fontSize: 12 }}>自动刷新</Text>
              <Switch checked={autoRefresh} onChange={setAutoRefresh} size="small" />
            </Space>
            <Button icon={<ReloadOutlined />} onClick={fetchLogs} loading={loading}>
              刷新
            </Button>
          </Space>
        }
      />

      {/* Filters */}
      <Card style={{ marginBottom: 16 }}>
        <Space wrap>
          <RangePicker
            value={dateRange}
            onChange={(dates) => {
              setDateRange(dates as [dayjs.Dayjs, dayjs.Dayjs] | null);
            }}
            placeholder={['开始日期', '结束日期']}
            allowClear
          />
          <Select
            placeholder="操作类型"
            allowClear
            style={{ width: 140 }}
            value={filterAction}
            onChange={(v) => {
              setFilterAction(v);
            }}
            options={actionOptions}
          />
          <Input
            placeholder="搜索用户"
            allowClear
            style={{ width: 180 }}
            prefix={<SearchOutlined />}
            value={filterUser}
            onChange={(e) => setFilterUser(e.target.value)}
          />
          <Button type="primary" onClick={handleFilter}>
            查询
          </Button>
        </Space>
      </Card>

      <Card>
        <Table<LogEntry>
          columns={columns}
          dataSource={logs}
          rowKey="id"
          loading={loading}
          scroll={{ x: 900 }}
          expandable={{
            expandedRowRender: (record) => (
              <div style={{ padding: '8px 16px' }}>
                <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>
                  详情
                </Text>
                <pre
                  style={{
                    background: '#f5f5f5',
                    padding: 12,
                    borderRadius: 4,
                    fontSize: 12,
                    maxHeight: 240,
                    overflow: 'auto',
                    margin: 0,
                  }}
                >
                  {formatDetail(record.detail)}
                </pre>
              </div>
            ),
            rowExpandable: (record) =>
              record.detail !== null && record.detail !== undefined && record.detail !== '',
          }}
          pagination={{
            current: page,
            pageSize,
            total,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (t) => `共 ${t} 条日志`,
            onChange,
          }}
        />
      </Card>
    </>
  );
};

export default AdminLogPage;
