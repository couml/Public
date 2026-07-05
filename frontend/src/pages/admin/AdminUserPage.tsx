import React, { useEffect, useState, useCallback } from 'react';
import {
  Table,
  Button,
  Modal,
  Form,
  Input,
  Select,
  Switch,
  Space,
  Popconfirm,
  message,
  Tag,
  Card,
} from 'antd';
import { EditOutlined, StopOutlined, ReloadOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import PageHeader from '@/components/PageHeader';
import { adminApi } from '@/api/admin';
import { formatDate } from '@/utils/format';
import { usePagination } from '@/hooks/usePagination';
import type { User } from '@/types/user';

const roleOptions = [
  { label: '管理员', value: 'admin' },
  { label: 'IT 人员', value: 'it_staff' },
  { label: '普通用户', value: 'user' },
];

const roleColorMap: Record<string, string> = {
  admin: 'red',
  it_staff: 'blue',
  user: 'default',
};

const AdminUserPage: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [filterRole, setFilterRole] = useState<string | undefined>(undefined);
  const [filterActive, setFilterActive] = useState<boolean | undefined>(undefined);
  const [form] = Form.useForm();
  const { page, pageSize, onChange, reset } = usePagination(20);

  const fetchUsers = useCallback(async () => {
    setLoading(true);
    try {
      const params: any = { page, page_size: pageSize };
      if (filterRole) params.role = filterRole;
      if (filterActive !== undefined) params.is_active = filterActive;
      const data = await adminApi.listUsers(params);
      setUsers(data.items);
      setTotal(data.total);
    } catch (err: any) {
      message.error(err?.response?.data?.message || '获取用户列表失败');
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, filterRole, filterActive]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const handleEdit = (record: User) => {
    setEditingUser(record);
    form.setFieldsValue({
      full_name: record.full_name,
      department: record.department,
      role: record.role,
      is_active: record.is_active,
    });
    setModalOpen(true);
  };

  const handleDeactivate = async (record: User) => {
    try {
      await adminApi.updateUser(record.id, { is_active: false });
      message.success(`用户 "${record.username}" 已停用`);
      fetchUsers();
    } catch (err: any) {
      message.error(err?.response?.data?.message || '操作失败');
    }
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setSubmitting(true);
      if (editingUser) {
        await adminApi.updateUser(editingUser.id, values);
        message.success('用户信息已更新');
      }
      setModalOpen(false);
      fetchUsers();
    } catch (err: any) {
      if (err?.errorFields) return;
      message.error(err?.response?.data?.message || '操作失败');
    } finally {
      setSubmitting(false);
    }
  };

  const handleFilterChange = () => {
    reset();
  };

  const columns: ColumnsType<User> = [
    { title: '用户名', dataIndex: 'username', key: 'username', width: 120 },
    {
      title: '姓名',
      dataIndex: 'full_name',
      key: 'full_name',
      width: 100,
      render: (v: string | null) => v || '-',
    },
    { title: '邮箱', dataIndex: 'email', key: 'email', width: 200, ellipsis: true },
    {
      title: '角色',
      dataIndex: 'role',
      key: 'role',
      width: 100,
      render: (role: string) => {
        const opt = roleOptions.find((r) => r.value === role);
        return <Tag color={roleColorMap[role] || 'default'}>{opt?.label || role}</Tag>;
      },
    },
    {
      title: '部门',
      dataIndex: 'department',
      key: 'department',
      width: 100,
      render: (v: string | null) => v || '-',
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 70,
      render: (active: boolean, record: User) => (
        <Popconfirm
          title={active ? '确认停用' : '确认启用'}
          description={`确定要${active ? '停用' : '启用'}用户 "${record.username}" 吗？`}
          onConfirm={() =>
            adminApi
              .updateUser(record.id, { is_active: !active })
              .then(() => {
                message.success(`用户已${active ? '停用' : '启用'}`);
                fetchUsers();
              })
              .catch((err) => message.error(err?.response?.data?.message || '操作失败'))
          }
          okText="确认"
          cancelText="取消"
        >
          <Switch checked={active} size="small" />
        </Popconfirm>
      ),
    },
    {
      title: '注册时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
      render: (v: string) => formatDate(v),
    },
    {
      title: '操作',
      key: 'actions',
      width: 140,
      fixed: 'right',
      render: (_: unknown, record: User) => (
        <Space size="small">
          <Button type="link" size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)}>
            编辑
          </Button>
          {record.is_active && (
            <Popconfirm
              title="确认停用"
              description={`确定要停用用户 "${record.username}" 吗？`}
              onConfirm={() => handleDeactivate(record)}
              okText="停用"
              cancelText="取消"
              okButtonProps={{ danger: true }}
            >
              <Button type="link" size="small" danger icon={<StopOutlined />}>
                停用
              </Button>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];

  return (
    <>
      <PageHeader
        title="用户管理"
        extra={
          <Button icon={<ReloadOutlined />} onClick={fetchUsers} loading={loading}>
            刷新
          </Button>
        }
      />

      {/* Filters */}
      <Card style={{ marginBottom: 16 }}>
        <Space wrap>
          <Select
            placeholder="筛选角色"
            allowClear
            style={{ width: 140 }}
            value={filterRole}
            onChange={(v) => {
              setFilterRole(v);
              handleFilterChange();
            }}
            options={roleOptions}
          />
          <Select
            placeholder="筛选状态"
            allowClear
            style={{ width: 140 }}
            value={filterActive}
            onChange={(v) => {
              setFilterActive(v);
              handleFilterChange();
            }}
            options={[
              { label: '启用', value: true },
              { label: '停用', value: false },
            ]}
          />
        </Space>
      </Card>

      <Card>
        <Table<User>
          columns={columns}
          dataSource={users}
          rowKey="id"
          loading={loading}
          scroll={{ x: 1000 }}
          pagination={{
            current: page,
            pageSize,
            total,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (t) => `共 ${t} 个用户`,
            onChange,
          }}
        />
      </Card>

      <Modal
        title="编辑用户"
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        onOk={handleSubmit}
        confirmLoading={submitting}
        width={480}
        destroyOnClose
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item name="full_name" label="姓名">
            <Input placeholder="用户姓名" />
          </Form.Item>
          <Form.Item name="department" label="部门">
            <Input placeholder="所属部门" />
          </Form.Item>
          <Form.Item name="role" label="角色" rules={[{ required: true, message: '请选择角色' }]}>
            <Select placeholder="选择角色" options={roleOptions} />
          </Form.Item>
          <Form.Item name="is_active" label="启用状态" valuePropName="checked">
            <Switch checkedChildren="启用" unCheckedChildren="停用" />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
};

export default AdminUserPage;
