import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card,
  Button,
  Tag,
  Space,
  Typography,
  Descriptions,
  Spin,
  Result,
  Divider,
  Empty,
  Skeleton,
} from 'antd';
import {
  ArrowLeftOutlined,
  ExportOutlined,
  RobotOutlined,
  UserOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons';
import PageHeader from '@/components/PageHeader';
import { diagnosisApi } from '@/api/diagnosis';
import type { DiagnosisSession, DiagnosisMessage } from '@/types/diagnosis';
import dayjs from 'dayjs';

const { Text, Paragraph, Title } = Typography;

const SESSION_STATUS: Record<string, { color: string; label: string }> = {
  active: { color: 'processing', label: '进行中' },
  resolved: { color: 'success', label: '已解决' },
  closed: { color: 'default', label: '已关闭' },
};

// ---------- Chat Bubble (simplified for report) ----------

interface ReportChatBubbleProps {
  message: DiagnosisMessage;
}

const ReportChatBubble: React.FC<ReportChatBubbleProps> = ({ message: msg }) => {
  const isUser = msg.role === 'user';

  return (
    <div
      style={{
        display: 'flex',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        marginBottom: 20,
      }}
    >
      {!isUser && (
        <div
          style={{
            width: 36,
            height: 36,
            borderRadius: '50%',
            background: '#f0f5ff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginRight: 10,
            flexShrink: 0,
            color: '#1677ff',
            fontSize: 18,
          }}
        >
          <RobotOutlined />
        </div>
      )}
      <div style={{ maxWidth: '70%' }}>
        <div
          style={{
            padding: '10px 16px',
            borderRadius: 12,
            background: isUser ? '#1677ff' : '#ffffff',
            color: isUser ? '#fff' : '#262626',
            border: isUser ? 'none' : '1px solid #f0f0f0',
            wordBreak: 'break-word',
            whiteSpace: 'pre-wrap',
            boxShadow: isUser
              ? '0 1px 4px rgba(22,119,255,0.3)'
              : '0 1px 4px rgba(0,0,0,0.06)',
          }}
        >
          {msg.message}
        </div>
        {msg.diagnosis_result && (
          <div
            style={{
              marginTop: 8,
              padding: 12,
              background: '#fafafa',
              borderRadius: 8,
              border: '1px solid #f0f0f0',
              fontSize: 13,
            }}
          >
            <Text type="secondary" style={{ fontSize: 11 }}>
              诊断结果
            </Text>
            <Paragraph style={{ margin: '4px 0 0' }}>
              {msg.diagnosis_result.fault_type} (置信度:{' '}
              {Math.round(msg.diagnosis_result.confidence * 100)}%)
            </Paragraph>
          </div>
        )}
        <div
          style={{
            fontSize: 11,
            color: '#bfbfbf',
            marginTop: 4,
            textAlign: isUser ? 'right' : 'left',
            padding: '0 4px',
          }}
        >
          <ClockCircleOutlined style={{ marginRight: 4 }} />
          {dayjs(msg.created_at).format('YYYY-MM-DD HH:mm')}
        </div>
      </div>
      {isUser && (
        <div
          style={{
            width: 36,
            height: 36,
            borderRadius: '50%',
            background: '#e6f4ff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginLeft: 10,
            flexShrink: 0,
            color: '#1677ff',
            fontSize: 18,
          }}
        >
          <UserOutlined />
        </div>
      )}
    </div>
  );
};

// ---------- Main Page ----------

const DiagnosisReportPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [session, setSession] = useState<DiagnosisSession | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;

    const fetchSession = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await diagnosisApi.getSession(id);
        setSession(data);
      } catch {
        setError('无法加载诊断报告，请确认链接有效');
      } finally {
        setLoading(false);
      }
    };

    fetchSession();
  }, [id]);

  const handleDownloadReport = () => {
    if (!id) return;
    const url = diagnosisApi.getReportUrl(id);
    window.open(url, '_blank');
  };

  // ---------- Loading state ----------
  if (loading) {
    return (
      <div style={{ padding: 24 }}>
        <PageHeader
          title="诊断报告"
          breadcrumb={[
            { title: 'AI 诊断', path: '/diagnosis' },
            { title: '报告详情' },
          ]}
        />
        <Card>
          <Skeleton active avatar paragraph={{ rows: 1 }} />
          <Divider />
          <Skeleton active paragraph={{ rows: 8 }} />
        </Card>
      </div>
    );
  }

  // ---------- Error state ----------
  if (error || !session) {
    return (
      <div style={{ padding: 24 }}>
        <Result
          status="error"
          title="加载失败"
          subTitle={error || '未找到该诊断会话'}
          extra={
            <Button type="primary" onClick={() => navigate('/diagnosis')}>
              返回诊断
            </Button>
          }
        />
      </div>
    );
  }

  const statusCfg = SESSION_STATUS[session.status] || SESSION_STATUS.active;
  const messages = session.messages || [];
  const hasMessages = messages.length > 0;

  return (
    <div style={{ padding: 24 }}>
      <PageHeader
        title="诊断报告"
        breadcrumb={[
          { title: 'AI 诊断', path: '/diagnosis' },
          { title: '报告详情' },
        ]}
        extra={
          <Space>
            <Button
              icon={<ExportOutlined />}
              type="primary"
              onClick={handleDownloadReport}
            >
              下载报告
            </Button>
            <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/diagnosis')}>
              返回诊断
            </Button>
          </Space>
        }
      />

      {/* Session Summary */}
      <Card title="会话摘要" style={{ marginBottom: 24 }}>
        <Descriptions column={{ xs: 1, sm: 2, md: 3 }} bordered size="small">
          <Descriptions.Item label="会话标题">{session.session_title}</Descriptions.Item>
          <Descriptions.Item label="创建时间">
            {dayjs(session.created_at).format('YYYY-MM-DD HH:mm')}
          </Descriptions.Item>
          <Descriptions.Item label="状态">
            <Tag color={statusCfg.color}>{statusCfg.label}</Tag>
          </Descriptions.Item>
          {session.printer_id && (
            <Descriptions.Item label="关联打印机">
              <Tag>{session.printer_id}</Tag>
            </Descriptions.Item>
          )}
          <Descriptions.Item label="更新时间">
            {dayjs(session.updated_at).format('YYYY-MM-DD HH:mm')}
          </Descriptions.Item>
          <Descriptions.Item label="消息数">
            {messages.length}
          </Descriptions.Item>
        </Descriptions>

        {/* Error Codes */}
        {session.error_codes && session.error_codes.length > 0 && (
          <div style={{ marginTop: 16 }}>
            <Text type="secondary" style={{ fontSize: 12 }}>
              已分析错误码：
            </Text>
            <div style={{ marginTop: 4 }}>
              <Space wrap>
                {session.error_codes.map((code) => (
                  <Tag key={code} color="orange">
                    {code}
                  </Tag>
                ))}
              </Space>
            </div>
          </div>
        )}

        {/* Resolution Summary */}
        {session.resolution_summary && (
          <div style={{ marginTop: 16 }}>
            <Text type="secondary" style={{ fontSize: 12 }}>
              解决方案摘要：
            </Text>
            <Paragraph style={{ marginTop: 4, whiteSpace: 'pre-wrap' }}>
              {session.resolution_summary}
            </Paragraph>
          </div>
        )}
      </Card>

      {/* Conversation Transcript */}
      <Card title="对话记录">
        {!hasMessages ? (
          <Empty description="暂无对话记录" />
        ) : (
          <div style={{ padding: '0 16px' }}>
            {messages.map((msg) => (
              <ReportChatBubble key={msg.id} message={msg} />
            ))}
          </div>
        )}
      </Card>
    </div>
  );
};

export default DiagnosisReportPage;
