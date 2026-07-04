import React, { useState, useEffect, useCallback } from 'react';
import { Card, Form, Select, InputNumber, Radio, Switch, Input, Button, Table, Steps, Tag, Space, message, Popconfirm } from 'antd';
import { DeleteOutlined, RedoOutlined, SendOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import FileUploadZone from '@/components/FileUploadZone';
import UploadProgressList from '@/components/UploadProgressList';
import PrinterSelector from '@/components/PrinterSelector';
import { useChunkedUpload } from '@/hooks/useChunkedUpload';
import { filesApi } from '@/api/files';
import { printApi } from '@/api/print';
import { formatFileSize } from '@/utils/format';
import { PAPER_SIZES, N_UP_OPTIONS } from '@/utils/constants';
import type { FileRecord, PrintJob } from '@/types/print';
import dayjs from 'dayjs';

const PRINT_TARGET_FORMATS = [
  { label: '原格式', value: 'original' },
  { label: 'PDF', value: 'pdf' },
  { label: 'PCL', value: 'pcl' },
  { label: 'PostScript', value: 'ps' },
];

const JOB_STATUS_COLOR: Record<string, string> = {
  queued: 'blue',
  converting: 'purple',
  waiting: 'orange',
  printing: 'processing',
  completed: 'green',
  failed: 'red',
  cancelled: 'default',
};

const PrintPage: React.FC = () => {
  const { uploadFile } = useChunkedUpload();

  // ---------- Print settings ----------
  const [selectedPrinter, setSelectedPrinter] = useState<string | undefined>();
  const [targetFormat, setTargetFormat] = useState<string>('original');
  const [copies, setCopies] = useState<number>(1);
  const [colorMode, setColorMode] = useState<'color' | 'grayscale'>('color');
  const [duplex, setDuplex] = useState<boolean>(false);
  const [paperSize, setPaperSize] = useState<string>('A4');
  const [pageRange, setPageRange] = useState<string>('');
  const [nUp, setNUp] = useState<number>(1);
  const [orientation, setOrientation] = useState<'portrait' | 'landscape'>('portrait');
  const [pinCode, setPinCode] = useState<string>('');

  // ---------- Staging ----------
  const [stagingFiles, setStagingFiles] = useState<FileRecord[]>([]);
  const [stagingLoading, setStagingLoading] = useState(false);
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);

  // ---------- Print queue ----------
  const [recentJobs, setRecentJobs] = useState<PrintJob[]>([]);

  const fetchStaging = useCallback(async () => {
    setStagingLoading(true);
    try {
      const files = await filesApi.getStaging();
      setStagingFiles(files);
    } catch {
      message.error('获取暂存文件失败');
    } finally {
      setStagingLoading(false);
    }
  }, []);

  const fetchRecentJobs = useCallback(async () => {
    try {
      const res = await printApi.list({ page: 1, page_size: 10 });
      setRecentJobs(res.items);
    } catch {
      // silent poll
    }
  }, []);

  useEffect(() => {
    fetchStaging();
    fetchRecentJobs();
    const interval = setInterval(fetchRecentJobs, 3000);
    return () => clearInterval(interval);
  }, [fetchStaging, fetchRecentJobs]);

  // ---------- Handlers ----------

  const handleFilesSelected = async (files: File[]) => {
    for (const file of files) {
      await uploadFile(file);
    }
    fetchStaging();
  };

  const buildJobPayload = (fileId: string) => ({
    printer_id: selectedPrinter!,
    file_id: fileId,
    copies,
    color_mode: colorMode,
    duplex,
    paper_size: paperSize,
    page_range: pageRange || undefined,
    n_up: String(nUp),
    orientation,
    pin_code: pinCode || undefined,
  });

  const handlePrint = async (file: FileRecord) => {
    if (!selectedPrinter) {
      message.warning('请先选择打印机');
      return;
    }
    try {
      await printApi.submitJob(buildJobPayload(file.id));
      message.success('打印任务已提交');
      fetchRecentJobs();
    } catch {
      message.error('提交打印任务失败');
    }
  };

  const handleBatchPrint = async () => {
    if (!selectedPrinter) {
      message.warning('请先选择打印机');
      return;
    }
    if (selectedRowKeys.length === 0) {
      message.warning('请选择要打印的文件');
      return;
    }
    try {
      await Promise.all(
        selectedRowKeys.map((id) => printApi.submitJob(buildJobPayload(id as string)))
      );
      message.success(`已提交 ${selectedRowKeys.length} 个打印任务`);
      setSelectedRowKeys([]);
      fetchRecentJobs();
    } catch {
      message.error('批量提交失败');
    }
  };

  const handleDelete = async (fileId: string) => {
    try {
      await filesApi.deleteFile(fileId);
      message.success('文件已删除');
      fetchStaging();
    } catch {
      message.error('删除失败');
    }
  };

  const handleReconvert = async (fileId: string) => {
    try {
      await filesApi.convert(fileId, targetFormat);
      message.success('转换任务已提交');
      fetchStaging();
    } catch {
      message.error('重新转换失败');
    }
  };

  // ---------- Staging table columns ----------

  const stagingColumns: ColumnsType<FileRecord> = [
    {
      title: '文件名',
      dataIndex: 'original_filename',
      key: 'original_filename',
      ellipsis: true,
    },
    {
      title: '格式',
      dataIndex: 'converted_format',
      key: 'converted_format',
      width: 100,
      render: (fmt: string | null) =>
        fmt ? <Tag color="blue">{fmt.toUpperCase()}</Tag> : <Tag>原格式</Tag>,
    },
    {
      title: '页数',
      dataIndex: 'page_count',
      key: 'page_count',
      width: 80,
      render: (pages: number | null) => pages ?? '-',
    },
    {
      title: '大小',
      dataIndex: 'file_size',
      key: 'file_size',
      width: 100,
      render: (size: number) => formatFileSize(size),
    },
    {
      title: '转换时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 170,
      render: (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '操作',
      key: 'actions',
      width: 260,
      render: (_, record) => (
        <Space size="small">
          <Button type="primary" size="small" icon={<SendOutlined />} onClick={() => handlePrint(record)}>
            打印
          </Button>
          <Popconfirm title="确定删除该文件？" onConfirm={() => handleDelete(record.id)}>
            <Button size="small" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
          <Button size="small" icon={<RedoOutlined />} onClick={() => handleReconvert(record.id)}>
            重转
          </Button>
        </Space>
      ),
    },
  ];

  // ---------- Render ----------

  return (
    <div style={{ padding: 24 }}>
      {/* Section 1: File Upload Zone */}
      <Card title="文件上传" style={{ marginBottom: 24 }}>
        <FileUploadZone onFilesSelected={handleFilesSelected} />
        <div style={{ marginTop: 16 }}>
          <UploadProgressList />
        </div>
      </Card>

      {/* Section 2: Print Settings Panel */}
      <Card title="打印设置" style={{ marginBottom: 24 }}>
        <Form layout="vertical">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '0 24px' }}>
            <Form.Item label="打印机">
              <PrinterSelector value={selectedPrinter} onChange={setSelectedPrinter} filterOnline />
            </Form.Item>

            <Form.Item label="目标格式">
              <Select value={targetFormat} onChange={setTargetFormat} options={PRINT_TARGET_FORMATS} />
            </Form.Item>

            <Form.Item label="打印份数">
              <InputNumber min={1} max={999} value={copies} onChange={(v) => setCopies(v ?? 1)} style={{ width: '100%' }} />
            </Form.Item>

            <Form.Item label="色彩模式">
              <Radio.Group value={colorMode} onChange={(e) => setColorMode(e.target.value)}>
                <Radio.Button value="color">彩色</Radio.Button>
                <Radio.Button value="grayscale">黑白</Radio.Button>
              </Radio.Group>
            </Form.Item>

            <Form.Item label="双面打印">
              <Switch checked={duplex} onChange={setDuplex} checkedChildren="开" unCheckedChildren="关" />
            </Form.Item>

            <Form.Item label="纸张尺寸">
              <Select
                value={paperSize}
                onChange={setPaperSize}
                options={PAPER_SIZES.map((p) => ({ label: p.label, value: p.value }))}
              />
            </Form.Item>

            <Form.Item label="页面范围">
              <Input placeholder="如: 1-5, 7, 9-12" value={pageRange} onChange={(e) => setPageRange(e.target.value)} />
            </Form.Item>

            <Form.Item label="N-Up">
              <Select
                value={nUp}
                onChange={setNUp}
                options={N_UP_OPTIONS.map((n) => ({ label: `${n.value}页/张`, value: n.value }))}
              />
            </Form.Item>

            <Form.Item label="方向">
              <Radio.Group value={orientation} onChange={(e) => setOrientation(e.target.value)}>
                <Radio.Button value="portrait">纵向</Radio.Button>
                <Radio.Button value="landscape">横向</Radio.Button>
              </Radio.Group>
            </Form.Item>

            <Form.Item label="PIN 码（安全打印）">
              <Input.Password placeholder="可选" value={pinCode} onChange={(e) => setPinCode(e.target.value)} />
            </Form.Item>
          </div>
        </Form>
      </Card>

      {/* Section 3: Staging Area */}
      <Card
        title="暂存区"
        style={{ marginBottom: 24 }}
        extra={
          <Button type="primary" onClick={handleBatchPrint} disabled={selectedRowKeys.length === 0}>
            一键打印所选 ({selectedRowKeys.length})
          </Button>
        }
      >
        <Table
          rowKey="id"
          columns={stagingColumns}
          dataSource={stagingFiles}
          loading={stagingLoading}
          rowSelection={{
            selectedRowKeys,
            onChange: (keys) => setSelectedRowKeys(keys),
          }}
          pagination={{ pageSize: 10, showTotal: (total) => `共 ${total} 个文件` }}
          locale={{ emptyText: '暂存区为空，请先上传文件' }}
        />
      </Card>

      {/* Section 4: Print Queue Tracker */}
      <Card title="打印队列">
        {recentJobs.length === 0 ? (
          <div style={{ textAlign: 'center', color: '#8c8c8c', padding: 24 }}>暂无打印任务</div>
        ) : (
          <Steps
            direction="vertical"
            size="small"
            current={-1}
            items={recentJobs.map((job) => ({
              title: (
                <Space>
                  <span>{job.job_name || job.id.slice(0, 8)}</span>
                  <Tag color={JOB_STATUS_COLOR[job.status] || 'default'}>{job.status}</Tag>
                </Space>
              ),
              description: `${dayjs(job.created_at).format('HH:mm:ss')}  ${job.pages_printed ?? 0}/${job.total_pages ?? '?'} 页`,
              status:
                job.status === 'failed'
                  ? ('error' as const)
                  : job.status === 'completed'
                    ? ('finish' as const)
                    : ('process' as const),
            }))}
          />
        )}
      </Card>
    </div>
  );
};

export default PrintPage;
