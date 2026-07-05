import React, { useEffect, useState, useCallback } from 'react';
import {
  Table,
  Button,
  Modal,
  Form,
  Input,
  Select,
  InputNumber,
  Switch,
  Space,
  Popconfirm,
  message,
  Progress,
  Tag,
  Card,
} from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, ReloadOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import PageHeader from '@/components/PageHeader';
import StatusBadge from '@/components/StatusBadge';
import { adminApi } from '@/api/admin';
import { PRINTER_BRANDS, PAPER_SIZES } from '@/utils/constants';
import { formatDate } from '@/utils/format';
import { usePagination } from '@/hooks/usePagination';
import type { Printer, DeviceStatus } from '@/types/device';

const AdminPrinterPage: React.FC = () => {
  const [printers, setPrinters] = useState<Printer[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingPrinter, setEditingPrinter] = useState<Printer | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [form] = Form.useForm();
  const { page, pageSize, onChange, reset } = usePagination(20);

  const fetchPrinters = useCallback(async () => {
    setLoading(true);
    try {
      const data = await adminApi.listPrinters({ page, page_size: pageSize });
      setPrinters(data.items);
      setTotal(data.total);
    } catch (err: any) {
      message.error(err?.response?.data?.message || '获取设备列表失败');
    } finally {
      setLoading(false);
    }
  }, [page, pageSize]);

  useEffect(() => {
    fetchPrinters();
  }, [fetchPrinters]);

  const handleAdd = () => {
    setEditingPrinter(null);
    form.resetFields();
    form.setFieldsValue({
      snmp_community: 'public',
      snmp_port: 161,
      supports_color: false,
      supports_duplex: false,
      max_paper_size: 'A4',
    });
    setModalOpen(true);
  };

  const handleEdit = (record: Printer) => {
    setEditingPrinter(record);
    form.setFieldsValue(record);
    setModalOpen(true);
  };

  const handleDelete = async (id: string) => {
    try {
      await adminApi.deletePrinter(id);
      message.success('设备已删除');
      reset();
      fetchPrinters();
    } catch (err: any) {
      message.error(err?.response?.data?.message || '删除设备失败');
    }
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setSubmitting(true);
      if (editingPrinter) {
        await adminApi.updatePrinter(editingPrinter.id, values);
        message.success('设备信息已更新');
      } else {
        await adminApi.createPrinter(values);
        message.success('设备已添加');
      }
      setModalOpen(false);
      reset();
      fetchPrinters();
    } catch (err: any) {
      if (err?.errorFields) return; // form validation error
      message.error(err?.response?.data?.message || '操作失败');
    } finally {
      setSubmitting(false);
    }
  };

  const columns: ColumnsType<Printer> = [
    { title: '名称', dataIndex: 'name', key: 'name', width: 140, ellipsis: true },
    { title: '品牌', dataIndex: 'brand', key: 'brand', width: 80 },
    { title: '型号', dataIndex: 'model', key: 'model', width: 100 },
    { title: 'IP 地址', dataIndex: 'ip_address', key: 'ip_address', width: 130 },
    { title: '位置', dataIndex: 'location', key: 'location', width: 100, ellipsis: true },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (status: DeviceStatus) => <StatusBadge status={status} />,
    },
    {
      title: '碳粉',
      dataIndex: 'toner_level',
      key: 'toner_level',
      width: 110,
      render: (level: number) => (
        <Progress
          percent={level}
          size="small"
          status={level <= 10 ? 'exception' : level <= 20 ? 'active' : 'normal'}
          format={(p) => `${p}%`}
        />
      ),
    },
    {
      title: '纸张',
      dataIndex: 'paper_level',
      key: 'paper_level',
      width: 110,
      render: (level: number) => (
        <Progress
          percent={level}
          size="small"
          status={level <= 5 ? 'exception' : level <= 15 ? 'active' : 'normal'}
          format={(p) => `${p}%`}
        />
      ),
    },
    {
      title: '最近上线',
      dataIndex: 'last_seen_at',
      key: 'last_seen_at',
      width: 150,
      render: (v: string | null) => (v ? formatDate(v) : '-'),
    },
    {
      title: '操作',
      key: 'actions',
      width: 120,
      fixed: 'right',
      render: (_: unknown, record: Printer) => (
        <Space size="small">
          <Button type="link" size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)}>
            编辑
          </Button>
          <Popconfirm
            title="确认删除"
            description={`确定要删除设备 "${record.name}" 吗？`}
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
        title="设备管理"
        extra={
          <Space>
            <Button icon={<ReloadOutlined />} onClick={fetchPrinters} loading={loading}>
              刷新
            </Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
              添加设备
            </Button>
          </Space>
        }
      />
      <Card>
        <Table<Printer>
          columns={columns}
          dataSource={printers}
          rowKey="id"
          loading={loading}
          scroll={{ x: 1200 }}
          pagination={{
            current: page,
            pageSize,
            total,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (t) => `共 ${t} 台设备`,
            onChange,
          }}
        />
      </Card>

      <Modal
        title={editingPrinter ? '编辑设备' : '添加设备'}
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        onOk={handleSubmit}
        confirmLoading={submitting}
        width={640}
        destroyOnClose
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item name="name" label="名称" rules={[{ required: true, message: '请输入设备名称' }]}>
            <Input placeholder="如 HP LaserJet Pro" />
          </Form.Item>
          <Form.Item name="brand" label="品牌" rules={[{ required: true, message: '请选择品牌' }]}>
            <Select placeholder="选择品牌" showSearch>
              {PRINTER_BRANDS.map((b) => (
                <Select.Option key={b} value={b}>{b}</Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="model" label="型号" rules={[{ required: true, message: '请输入型号' }]}>
            <Input placeholder="如 M404dn" />
          </Form.Item>
          <Form.Item name="serial_number" label="序列号">
            <Input placeholder="设备序列号" />
          </Form.Item>
          <Form.Item name="ip_address" label="IP 地址" rules={[{ required: true, message: '请输入 IP 地址' }]}>
            <Input placeholder="192.168.1.100" />
          </Form.Item>
          <Form.Item name="mac_address" label="MAC 地址">
            <Input placeholder="00:1A:2B:3C:4D:5E" />
          </Form.Item>
          <Form.Item name="location" label="位置">
            <Input placeholder="如 3楼A区" />
          </Form.Item>
          <Form.Item name="snmp_community" label="SNMP Community">
            <Input placeholder="public" />
          </Form.Item>
          <Form.Item name="snmp_port" label="SNMP 端口">
            <InputNumber min={1} max={65535} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="supports_color" label="支持彩色" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item name="supports_duplex" label="支持双面打印" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item name="max_paper_size" label="最大纸张尺寸">
            <Select placeholder="选择纸张尺寸">
              {PAPER_SIZES.map((p) => (
                <Select.Option key={p.value} value={p.value}>{p.label}</Select.Option>
              ))}
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
};

export default AdminPrinterPage;
