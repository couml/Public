import React, { useEffect, useState, useCallback } from 'react';
import {
  Table,
  Button,
  Modal,
  Form,
  Input,
  Select,
  DatePicker,
  Upload,
  Space,
  Popconfirm,
  message,
  Tag,
  Card,
} from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, ReloadOutlined, UploadOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import type { UploadFile } from 'antd/es/upload';
import dayjs from 'dayjs';
import PageHeader from '@/components/PageHeader';
import { adminApi } from '@/api/admin';
import { PRINTER_BRANDS } from '@/utils/constants';
import { formatFileSize, formatDate } from '@/utils/format';
import { usePagination } from '@/hooks/usePagination';
import type { DriverPackage } from '@/types/driver';

const { TextArea } = Input;

const OS_PLATFORMS = [
  { label: 'Windows', value: 'windows' },
  { label: 'macOS', value: 'macos' },
  { label: 'Linux', value: 'linux' },
];

const AdminDriverPage: React.FC = () => {
  const [drivers, setDrivers] = useState<DriverPackage[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingDriver, setEditingDriver] = useState<DriverPackage | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [form] = Form.useForm();
  const { page, pageSize, onChange, reset } = usePagination(20);

  const fetchDrivers = useCallback(async () => {
    setLoading(true);
    try {
      const data = await adminApi.listDrivers({ page, page_size: pageSize });
      setDrivers(data.items);
      setTotal(data.total);
    } catch (err: any) {
      message.error(err?.response?.data?.message || '获取驱动列表失败');
    } finally {
      setLoading(false);
    }
  }, [page, pageSize]);

  useEffect(() => {
    fetchDrivers();
  }, [fetchDrivers]);

  const handleAdd = () => {
    setEditingDriver(null);
    setFileList([]);
    form.resetFields();
    setModalOpen(true);
  };

  const handleEdit = (record: DriverPackage) => {
    setEditingDriver(record);
    setFileList([]);
    form.setFieldsValue({
      ...record,
      release_date: record.release_date ? dayjs(record.release_date) : undefined,
    });
    setModalOpen(true);
  };

  const handleDelete = async (id: string) => {
    try {
      await adminApi.deleteDriver(id);
      message.success('驱动已删除');
      reset();
      fetchDrivers();
    } catch (err: any) {
      message.error(err?.response?.data?.message || '删除驱动失败');
    }
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setSubmitting(true);

      if (editingDriver) {
        const payload = {
          ...values,
          release_date: values.release_date?.format('YYYY-MM-DD'),
        };
        await adminApi.updateDriver(editingDriver.id, payload);
        message.success('驱动信息已更新');
      } else {
        if (fileList.length === 0) {
          message.error('请上传驱动文件');
          setSubmitting(false);
          return;
        }
        const formData = new FormData();
        formData.append('brand', values.brand);
        formData.append('model', values.model);
        formData.append('os_platform', values.os_platform);
        formData.append('version', values.version);
        if (values.release_date) {
          formData.append('release_date', values.release_date.format('YYYY-MM-DD'));
        }
        if (values.changelog) {
          formData.append('changelog', values.changelog);
        }
        formData.append('file', fileList[0].originFileObj as File);
        await adminApi.createDriver(formData);
        message.success('驱动已上传');
      }
      setModalOpen(false);
      reset();
      fetchDrivers();
    } catch (err: any) {
      if (err?.errorFields) return;
      message.error(err?.response?.data?.message || '操作失败');
    } finally {
      setSubmitting(false);
    }
  };

  const columns: ColumnsType<DriverPackage> = [
    { title: '品牌', dataIndex: 'brand', key: 'brand', width: 80 },
    { title: '型号', dataIndex: 'model', key: 'model', width: 120 },
    {
      title: '操作系统',
      dataIndex: 'os_platform',
      key: 'os_platform',
      width: 100,
      render: (v: string) => {
        const label = OS_PLATFORMS.find((o) => o.value === v)?.label || v;
        return <Tag>{label}</Tag>;
      },
    },
    { title: '版本', dataIndex: 'version', key: 'version', width: 90 },
    {
      title: '文件大小',
      dataIndex: 'file_size',
      key: 'file_size',
      width: 90,
      render: (v: number) => formatFileSize(v),
    },
    {
      title: '发布日期',
      dataIndex: 'release_date',
      key: 'release_date',
      width: 110,
      render: (v: string) => (v ? formatDate(v) : '-'),
    },
    {
      title: '下载次数',
      dataIndex: 'download_count',
      key: 'download_count',
      width: 90,
      sorter: (a, b) => a.download_count - b.download_count,
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 80,
      render: (active: boolean) =>
        active ? <Tag color="green">启用</Tag> : <Tag color="default">停用</Tag>,
    },
    {
      title: '操作',
      key: 'actions',
      width: 120,
      fixed: 'right',
      render: (_: unknown, record: DriverPackage) => (
        <Space size="small">
          <Button type="link" size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)}>
            编辑
          </Button>
          <Popconfirm
            title="确认删除"
            description={`确定要删除驱动 "${record.brand} ${record.model} v${record.version}" 吗？`}
            onConfirm={() => handleDelete(record.id)}
            okText="删除"
            cancelText="取消"
            okButtonProps={{ danger: true }}
          >
            <Button type="link" size="small" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <>
      <PageHeader
        title="驱动管理"
        extra={
          <Space>
            <Button icon={<ReloadOutlined />} onClick={fetchDrivers} loading={loading}>
              刷新
            </Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
              上传驱动
            </Button>
          </Space>
        }
      />
      <Card>
        <Table<DriverPackage>
          columns={columns}
          dataSource={drivers}
          rowKey="id"
          loading={loading}
          scroll={{ x: 1000 }}
          pagination={{
            current: page,
            pageSize,
            total,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (t) => `共 ${t} 个驱动`,
            onChange,
          }}
        />
      </Card>

      <Modal
        title={editingDriver ? '编辑驱动' : '上传驱动'}
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        onOk={handleSubmit}
        confirmLoading={submitting}
        width={600}
        destroyOnClose
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item name="brand" label="品牌" rules={[{ required: true, message: '请选择品牌' }]}>
            <Select placeholder="选择品牌" showSearch>
              {PRINTER_BRANDS.map((b) => (
                <Select.Option key={b} value={b}>{b}</Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="model" label="型号" rules={[{ required: true, message: '请输入型号' }]}>
            <Input placeholder="如 LaserJet Pro M404dn" />
          </Form.Item>
          <Form.Item name="os_platform" label="操作系统" rules={[{ required: true, message: '请选择操作系统' }]}>
            <Select placeholder="选择操作系统">
              {OS_PLATFORMS.map((o) => (
                <Select.Option key={o.value} value={o.value}>{o.label}</Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="version" label="版本号" rules={[{ required: true, message: '请输入版本号' }]}>
            <Input placeholder="如 1.0.0" />
          </Form.Item>
          <Form.Item name="release_date" label="发布日期">
            <DatePicker style={{ width: '100%' }} placeholder="选择发布日期" />
          </Form.Item>
          <Form.Item name="changelog" label="更新日志">
            <TextArea rows={3} placeholder="此版本的更新内容..." />
          </Form.Item>

          {!editingDriver && (
            <Form.Item label="驱动文件" required>
              <Upload.Dragger
                fileList={fileList}
                beforeUpload={() => false}
                onChange={({ fileList: fl }) => setFileList(fl)}
                maxCount={1}
                accept=".exe,.dmg,.pkg,.deb,.rpm,.zip,.tar.gz,.msi"
              >
                <p className="ant-upload-drag-icon">
                  <UploadOutlined />
                </p>
                <p className="ant-upload-text">点击或拖拽驱动文件到此区域上传</p>
                <p className="ant-upload-hint">支持 exe, dmg, pkg, deb, rpm, zip, msi 等格式</p>
              </Upload.Dragger>
            </Form.Item>
          )}
        </Form>
      </Modal>
    </>
  );
};

export default AdminDriverPage;
