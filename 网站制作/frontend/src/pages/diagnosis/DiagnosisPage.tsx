import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Button,
  Input,
  List,
  Tag,
  Space,
  Typography,
  Skeleton,
  Progress,
  Steps,
  Alert,
  Badge,
  message,
  Spin,
  Empty,
} from 'antd';
import {
  PlusOutlined,
  SendOutlined,
  ExportOutlined,
  RobotOutlined,
  UserOutlined,
  DeleteOutlined,
} from '@ant-design/icons';
import PrinterSelector from '@/components/PrinterSelector';
import { diagnosisApi } from '@/api/diagnosis';
import { useAuthStore } from '@/store/authStore';
import type { DiagnosisSession, DiagnosisMessage, DiagnosisResult } from '@/types/diagnosis';
import dayjs from 'dayjs';

const { Text, Paragraph } = Typography;
const { TextArea } = Input;

// ---------- Severity color map ----------
const SEVERITY_COLOR: Record<string, string> = {
  info: '#1677ff',
  warning: '#faad14',
  critical: '#ff4d4f',
};

const SEVERITY_LABEL: Record<string, string> = {
  info: '信息',
  warning: '警告',
  critical: '严重',
};

const SESSION_STATUS: Record<string, { color: string; label: string }> = {
  active: { color: 'processing', label: '进行中' },
  resolved: { color: 'success', label: '已解决' },
  closed: { color: 'default', label: '已关闭' },
};

// ---------- DiagnosisResultCard ----------

interface DiagnosisResultCardProps {
  result: DiagnosisResult;
}

const DiagnosisResultCard: React.FC<DiagnosisResultCardProps> = ({ result }) => {
  const severityColor = SEVERITY_COLOR[result.severity] || '#8c8c8c';

  return (
    <div
      style={{
        marginTop: 12,
        padding: 16,
        background: '#fafafa',
        borderRadius: 8,
        border: '1px solid #f0f0f0',
      }}
    >
      <Space direction="vertical" size={12} style={{ width: '100%' }}>
        {/* Fault Type */}
        <div>
          <Text type="secondary" style={{ fontSize: 12 }}>
            故障类型
          </Text>
          <br />
          <Tag color={severityColor} style={{ marginTop: 2 }}>
            {SEVERITY_LABEL[result.severity]}: {result.fault_type}
          </Tag>
        </div>

        {/* Root Cause */}
        <div>
          <Text type="secondary" style={{ fontSize: 12 }}>
            根因分析
          </Text>
          <Paragraph style={{ margin: '4px 0 0', whiteSpace: 'pre-wrap' }}>
            {result.root_cause}
          </Paragraph>
        </div>

        {/* Confidence */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <Text type="secondary" style={{ fontSize: 12 }}>
            置信度
          </Text>
          <Progress
            type="circle"
            percent={Math.round(result.confidence * 100)}
            size={48}
            strokeColor={severityColor}
          />
        </div>

        {/* Repair Steps */}
        {result.steps && result.steps.length > 0 && (
          <div>
            <Text type="secondary" style={{ fontSize: 12 }}>
              修复步骤
            </Text>
            <Steps
              direction="vertical"
              size="small"
              current={-1}
              style={{ marginTop: 8 }}
              items={result.steps.map((step, i) => ({
                title: step,
              }))}
            />
          </div>
        )}

        {/* Parts Needed */}
        {result.parts && result.parts.length > 0 && (
          <div>
            <Text type="secondary" style={{ fontSize: 12 }}>
              所需零件
            </Text>
            <List
              size="small"
              dataSource={result.parts}
              renderItem={(part) => (
                <List.Item style={{ padding: '2px 0' }}>
                  <Tag>{part}</Tag>
                </List.Item>
              )}
              style={{ marginTop: 4 }}
            />
          </div>
        )}

        {/* Safety Warnings */}
        {result.safety && result.safety.length > 0 && (
          <div>
            {result.safety.map((warning, i) => (
              <Alert
                key={i}
                message={warning}
                type="warning"
                showIcon
                style={{ marginTop: 4 }}
              />
            ))}
          </div>
        )}
      </Space>
    </div>
  );
};

// ---------- Chat Bubble ----------

interface ChatBubbleProps {
  message: DiagnosisMessage;
}

const ChatBubble: React.FC<ChatBubbleProps> = ({ message: msg }) => {
  const isUser = msg.role === 'user';

  return (
    <div
      style={{
        display: 'flex',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        marginBottom: 16,
      }}
    >
      {/* AI avatar */}
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

      <div style={{ maxWidth: '75%' }}>
        {/* Bubble */}
        <div
          style={{
            padding: '10px 16px',
            borderRadius: 12,
            background: isUser ? '#1677ff' : '#ffffff',
            color: isUser ? '#fff' : '#262626',
            border: isUser ? 'none' : '1px solid #f0f0f0',
            wordBreak: 'break-word',
            whiteSpace: 'pre-wrap',
            boxShadow: isUser ? '0 1px 4px rgba(22,119,255,0.3)' : '0 1px 4px rgba(0,0,0,0.06)',
          }}
        >
          {msg.message}
        </div>

        {/* Diagnosis result */}
        {msg.diagnosis_result && <DiagnosisResultCard result={msg.diagnosis_result} />}

        {/* Timestamp */}
        <div
          style={{
            fontSize: 11,
            color: '#bfbfbf',
            marginTop: 4,
            textAlign: isUser ? 'right' : 'left',
            padding: '0 4px',
          }}
        >
          {dayjs(msg.created_at).format('HH:mm')}
        </div>
      </div>

      {/* User avatar */}
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

const DiagnosisPage: React.FC = () => {
  const user = useAuthStore((s) => s.user);

  const [sessions, setSessions] = useState<DiagnosisSession[]>([]);
  const [sessionsLoading, setSessionsLoading] = useState(false);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<DiagnosisMessage[]>([]);
  const [messagesLoading, setMessagesLoading] = useState(false);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [associatedPrinter, setAssociatedPrinter] = useState<string | undefined>();

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<any>(null);

  // ---------- Scroll to bottom ----------
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading, scrollToBottom]);

  // ---------- Fetch sessions ----------
  const fetchSessions = useCallback(async () => {
    setSessionsLoading(true);
    try {
      const res = await diagnosisApi.listSessions({ page: 1, page_size: 50 });
      setSessions(res.items);
    } catch {
      message.error('获取诊断会话失败');
    } finally {
      setSessionsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  // ---------- Fetch messages for active session ----------
  const fetchMessages = useCallback(async (sessionId: string) => {
    setMessagesLoading(true);
    try {
      const session = await diagnosisApi.getSession(sessionId);
      setMessages(session.messages || []);
      if (session.printer_id) {
        setAssociatedPrinter(session.printer_id);
      }
    } catch {
      message.error('获取消息记录失败');
    } finally {
      setMessagesLoading(false);
    }
  }, []);

  useEffect(() => {
    if (activeSessionId) {
      fetchMessages(activeSessionId);
    } else {
      setMessages([]);
    }
  }, [activeSessionId, fetchMessages]);

  // ---------- Create new session ----------
  const handleNewSession = async () => {
    try {
      const session = await diagnosisApi.createSession({
        printer_id: associatedPrinter,
        title: `诊断 ${dayjs().format('MM-DD HH:mm')}`,
      });
      setSessions((prev) => [session, ...prev]);
      setActiveSessionId(session.id);
      setMessages([]);
      setInputValue('');
    } catch {
      message.error('创建诊断会话失败');
    }
  };

  // ---------- Send message ----------
  const handleSend = async () => {
    const text = inputValue.trim();
    if (!text || isLoading) return;

    if (!activeSessionId) {
      await handleNewSession();
      // After creating, activeSessionId will be set, but this function won't re-run automatically.
      // We'll set a flag and retry via useEffect.
      return;
    }

    const userMsg: DiagnosisMessage = {
      id: `temp_${Date.now()}`,
      session_id: activeSessionId,
      role: 'user',
      message: text,
      diagnosis_result: null,
      sources: [],
      step_number: null,
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputValue('');
    setIsLoading(true);

    try {
      const aiResponse = await diagnosisApi.sendMessage(activeSessionId, text);
      setMessages((prev) => [...prev, aiResponse]);
      // Refresh sessions to update title/status
      fetchSessions();
    } catch {
      message.error('发送消息失败，请重试');
    } finally {
      setIsLoading(false);
    }
  };

  // Handle the case where user sends message without active session
  useEffect(() => {
    if (activeSessionId && inputValue.trim() && !isLoading) {
      // This effect handles the case where handleSend created a session
      // but the message wasn't sent yet. We need the user to click send again.
      // Actually, let's handle this differently.
    }
  }, [activeSessionId]);

  // Improved send that auto-creates session then sends
  const handleSendWrapper = async () => {
    const text = inputValue.trim();
    if (!text || isLoading) return;

    if (!activeSessionId) {
      // Create session first, then send
      try {
        setIsLoading(true);
        const session = await diagnosisApi.createSession({
          printer_id: associatedPrinter,
          title: `诊断 ${dayjs().format('MM-DD HH:mm')}`,
        });
        setSessions((prev) => [session, ...prev]);
        setActiveSessionId(session.id);

        const userMsg: DiagnosisMessage = {
          id: `temp_${Date.now()}`,
          session_id: session.id,
          role: 'user',
          message: text,
          diagnosis_result: null,
          sources: [],
          step_number: null,
          created_at: new Date().toISOString(),
        };

        setMessages([userMsg]);
        setInputValue('');

        const aiResponse = await diagnosisApi.sendMessage(session.id, text);
        setMessages((prev) => [...prev, aiResponse]);
        fetchSessions();
      } catch {
        message.error('操作失败，请重试');
      } finally {
        setIsLoading(false);
      }
      return;
    }

    handleSend();
  };

  // ---------- Keyboard handler ----------
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendWrapper();
    }
  };

  // ---------- Export report ----------
  const handleExportReport = () => {
    if (!activeSessionId) {
      message.warning('请先选择一个诊断会话');
      return;
    }
    const url = diagnosisApi.getReportUrl(activeSessionId);
    window.open(url, '_blank');
  };

  // ---------- Active session info ----------
  const activeSession = sessions.find((s) => s.id === activeSessionId);

  // ---------- Render ----------

  return (
    <div style={{ display: 'flex', height: 'calc(100vh - 64px)', overflow: 'hidden' }}>
      {/* ========== Left Sidebar ========== */}
      <div
        style={{
          width: 320,
          minWidth: 320,
          borderRight: '1px solid #f0f0f0',
          display: 'flex',
          flexDirection: 'column',
          background: '#fafafa',
        }}
      >
        {/* Header */}
        <div style={{ padding: 16, borderBottom: '1px solid #f0f0f0' }}>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            block
            onClick={handleNewSession}
          >
            新建诊断
          </Button>
          <div style={{ marginTop: 12 }}>
            <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>
              关联打印机
            </Text>
            <PrinterSelector
              value={associatedPrinter}
              onChange={setAssociatedPrinter}
            />
          </div>
        </div>

        {/* Session List */}
        <div style={{ flex: 1, overflowY: 'auto' }}>
          {sessionsLoading ? (
            <div style={{ padding: 16 }}>
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} active avatar paragraph={{ rows: 1 }} style={{ marginBottom: 12 }} />
              ))}
            </div>
          ) : sessions.length === 0 ? (
            <Empty
              description="暂无诊断记录"
              style={{ marginTop: 60 }}
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            />
          ) : (
            <List
              dataSource={sessions}
              renderItem={(session) => {
                const isActive = session.id === activeSessionId;
                const statusCfg = SESSION_STATUS[session.status] || SESSION_STATUS.active;
                return (
                  <div
                    onClick={() => setActiveSessionId(session.id)}
                    style={{
                      padding: '12px 16px',
                      cursor: 'pointer',
                      borderBottom: '1px solid #f0f0f0',
                      background: isActive ? '#e6f4ff' : 'transparent',
                      borderLeft: isActive ? '3px solid #1677ff' : '3px solid transparent',
                      transition: 'all 0.2s',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 4 }}>
                      <Text
                        strong
                        ellipsis
                        style={{
                          maxWidth: 180,
                          color: isActive ? '#1677ff' : '#262626',
                        }}
                      >
                        {session.session_title}
                      </Text>
                      <Badge status={statusCfg.color as any} text={statusCfg.label} />
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {dayjs(session.created_at).format('MM-DD HH:mm')}
                      </Text>
                      {session.error_codes && session.error_codes.length > 0 && (
                        <Space size={2} wrap>
                          {session.error_codes.slice(0, 2).map((code) => (
                            <Tag key={code} color="orange" style={{ fontSize: 10 }}>
                              {code}
                            </Tag>
                          ))}
                        </Space>
                      )}
                    </div>
                  </div>
                );
              }}
            />
          )}
        </div>
      </div>

      {/* ========== Right Chat Area ========== */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', background: '#f5f5f5' }}>
        {/* Chat Header */}
        <div
          style={{
            padding: '12px 24px',
            borderBottom: '1px solid #f0f0f0',
            background: '#fff',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <Space>
            <Text strong style={{ fontSize: 16 }}>
              {activeSession ? activeSession.session_title : 'AI 故障诊断'}
            </Text>
            {activeSession && (
              <Badge
                status={SESSION_STATUS[activeSession.status]?.color as any}
                text={SESSION_STATUS[activeSession.status]?.label}
              />
            )}
          </Space>
          <Button
            icon={<ExportOutlined />}
            onClick={handleExportReport}
            disabled={!activeSessionId || messages.length === 0}
          >
            导出报告
          </Button>
        </div>

        {/* Messages Area */}
        <div
          style={{
            flex: 1,
            overflowY: 'auto',
            padding: 24,
            background: '#f5f5f5',
          }}
        >
          {!activeSessionId ? (
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                height: '100%',
                color: '#bfbfbf',
              }}
            >
              <RobotOutlined style={{ fontSize: 48, marginBottom: 16 }} />
              <Text type="secondary" style={{ fontSize: 16 }}>
                选择一个诊断会话或创建新的诊断
              </Text>
            </div>
          ) : messagesLoading ? (
            <div style={{ padding: 24 }}>
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton
                  key={i}
                  active
                  avatar
                  paragraph={{ rows: 2 }}
                  style={{ marginBottom: 24 }}
                />
              ))}
            </div>
          ) : (
            <>
              {messages.length === 0 && !isLoading && (
                <div style={{ textAlign: 'center', paddingTop: 60 }}>
                  <RobotOutlined style={{ fontSize: 36, color: '#d9d9d9', marginBottom: 12 }} />
                  <br />
                  <Text type="secondary">描述你的打印机故障，AI 将为你诊断</Text>
                </div>
              )}

              {messages.map((msg) => (
                <ChatBubble key={msg.id} message={msg} />
              ))}

              {/* Loading indicator */}
              {isLoading && (
                <div style={{ display: 'flex', alignItems: 'flex-start', marginBottom: 16 }}>
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
                  <div style={{ maxWidth: '75%' }}>
                    <Skeleton active paragraph={{ rows: 2 }} />
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Input Area */}
        {activeSessionId && (
          <div
            style={{
              padding: '12px 24px',
              borderTop: '1px solid #f0f0f0',
              background: '#fff',
            }}
          >
            <div style={{ display: 'flex', gap: 12, alignItems: 'flex-end' }}>
              <TextArea
                ref={inputRef}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="描述故障现象，按 Enter 发送，Shift+Enter 换行"
                autoSize={{ minRows: 1, maxRows: 4 }}
                style={{ flex: 1 }}
                disabled={isLoading}
              />
              <Button
                type="primary"
                icon={<SendOutlined />}
                onClick={handleSendWrapper}
                loading={isLoading}
                disabled={!inputValue.trim()}
              >
                发送
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DiagnosisPage;
