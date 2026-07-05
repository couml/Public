import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Form, Input, Button, Card, Typography, message } from 'antd';
import { UserOutlined, LockOutlined, MailOutlined, IdcardOutlined, PrinterOutlined } from '@ant-design/icons';
import { useAuthStore } from '@/store/authStore';

const { Title, Text } = Typography;

export default function RegisterPage() {
  const [loading, setLoading] = useState(false);
  const register = useAuthStore((s) => s.register);
  const navigate = useNavigate();

  const onFinish = async (values: { username: string; email: string; password: string; full_name?: string }) => {
    setLoading(true);
    try {
      await register(values.username, values.email, values.password, values.full_name);
      message.success('注册成功');
      navigate('/dashboard');
    } catch (error: any) {
      const msg = error?.response?.data?.detail || '注册失败';
      message.error(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    }}>
      <Card style={{ width: 420, borderRadius: 12, boxShadow: '0 8px 32px rgba(0,0,0,0.1)' }}>
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <PrinterOutlined style={{ fontSize: 48, color: '#1677ff' }} />
          <Title level={3} style={{ marginTop: 16, marginBottom: 4 }}>创建账号</Title>
          <Text type="secondary">注册智慧打印机管理平台</Text>
        </div>

        <Form name="register" onFinish={onFinish} size="large" autoComplete="off">
          <Form.Item name="username" rules={[
            { required: true, message: '请输入用户名' },
            { min: 3, max: 64, message: '用户名长度 3-64 个字符' },
          ]}>
            <Input prefix={<UserOutlined />} placeholder="用户名" />
          </Form.Item>

          <Form.Item name="full_name" rules={[{ required: false }]}>
            <Input prefix={<IdcardOutlined />} placeholder="姓名（选填）" />
          </Form.Item>

          <Form.Item name="email" rules={[
            { required: true, message: '请输入邮箱' },
            { type: 'email', message: '邮箱格式不正确' },
          ]}>
            <Input prefix={<MailOutlined />} placeholder="邮箱" />
          </Form.Item>

          <Form.Item name="password" rules={[
            { required: true, message: '请输入密码' },
            { min: 8, message: '密码至少 8 个字符' },
          ]}>
            <Input.Password prefix={<LockOutlined />} placeholder="密码" />
          </Form.Item>

          <Form.Item name="confirm" dependencies={['password']} rules={[
            { required: true, message: '请确认密码' },
            ({ getFieldValue }) => ({
              validator(_, value) {
                if (!value || getFieldValue('password') === value) {
                  return Promise.resolve();
                }
                return Promise.reject(new Error('两次输入的密码不一致'));
              },
            }),
          ]}>
            <Input.Password prefix={<LockOutlined />} placeholder="确认密码" />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block>
              注 册
            </Button>
          </Form.Item>

          <div style={{ textAlign: 'center' }}>
            <Link to="/login">已有账号？立即登录</Link>
          </div>
        </Form>
      </Card>
    </div>
  );
}
