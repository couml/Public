import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Row,
  Col,
  Card,
  Button,
  Tag,
  Typography,
  Descriptions,
  Select,
  Spin,
  Alert,
  Collapse,
  Modal,
  Space,
  message,
} from 'antd';
import {
  FilePdfOutlined,
  FileImageOutlined,
  FileTextOutlined,
  DownloadOutlined,
  ScanOutlined,
  ShareAltOutlined,
  ArrowLeftOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  SyncOutlined,
  CloseCircleOutlined,
  CopyOutlined,
} from '@ant-design/icons';
import PageHeader from '@/components/PageHeader';
import EmptyState from '@/components/EmptyState';
import LoadingSkeleton from '@/components/LoadingSkeleton';
import { documentsApi } from '@/api/documents';
import { formatFileSize, formatDate } from '@/utils/format';
import type { ScanDocument } from '@/types/document';

const { Text, Title, Paragraph } = Typography;

const OCR_STATUS_CONFIG: Record<string, { color: string; icon: React.ReactNode; text: string }> = {
  pending: { color: 'default', icon: <ClockCircleOutlined />, text: '待识别' },
  processing: { color: 'processing', icon: <SyncOutlined spin />, text: '识别中' },
  completed: { color: 'success', icon: <CheckCircleOutlined />, text: '已识别' },
  failed: { color: 'error', icon: <CloseCircleOutlined />, text: '识别失败' },
};

const CATEGORY_OPTIONS = ['Contract', 'Report', 'Invoice', 'Other'];

function getPreviewIcon(mimeType: string | null) {
  if (!mimeType) return <FileTextOutlined style={{ fontSize: 80, color: '#bfbfbf' }} />;
  if (mimeType.includes('pdf')) {
    return <FilePdfOutlined style={{ fontSize: 80, color: '#ff4d4f' }} />;
  }
  if (mimeType.includes('image')) {
    return <FileImageOutlined style={{ fontSize: 80, color: '#1677ff' }} />;
  }
  return <FileTextOutlined style={{ fontSize: 80, color: '#bfbfbf' }} />;
}

const DocumentDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [document, setDocument] = useState<ScanDocument | null>(null);
  const [loading, setLoading] = useState(true);
  const [ocrLoading, setOcrLoading] = useState(false);
  const [shareModalOpen, setShareModalOpen] = useState(false);
  const [shareUrl, setShareUrl] = useState('');
  const [shareLoading, setShareLoading] = useState(false);
  const [editingTags, setEditingTags] = useState<string[]>([]);
  const [tagsChanged, setTagsChanged] = useState(false);
  const [tagsSaving, setTagsSaving] = useState(false);

  const fetchDocument = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    try {
      const data = await documentsApi.getById(id);
      setDocument(data);
      setEditingTags(data.tags || []);
      setTagsChanged(false);
    } catch (error) {
      console.error('Failed to fetch document:', error);
      setDocument(null);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchDocument();
  }, [fetchDocument]);

  // Poll for OCR status if currently processing
  useEffect(() => {
    if (!document || document.ocr_status !== 'processing') return;
    const interval = setInterval(() => {
      fetchDocument();
    }, 3000);
    return () => clearInterval(interval);
  }, [document?.ocr_status, fetchDocument]);

  const handleDownload = useCallback(() => {
    if (!document) return;
    const url = documentsApi.getDownloadUrl(document.id);
    window.open(url, '_blank');
    message.success('开始下载...');
  }, [document]);

  const handleTriggerOcr = useCallback(async () => {
    if (!document) return;
    setOcrLoading(true);
    try {
      await documentsApi.triggerOcr(document.id);
      message.success('OCR 识别任务已触发');
      setDocument((prev) => prev ? { ...prev, ocr_status: 'processing' } : prev);
    } catch {
      message.error('触发 OCR 失败');
    } finally {
      setOcrLoading(false);
    }
  }, [document]);

  const handleShare = useCallback(async () => {
    if (!document) return;
    setShareLoading(true);
    try {
      const result = await documentsApi.share(document.id);
      const token = result?.share_token || document.share_token;
      setShareUrl(`${window.location.origin}/documents/shared/${token}`);
      setShareModalOpen(true);
    } catch {
      message.error('生成分享链接失败');
    } finally {
      setShareLoading(false);
    }
  }, [document]);

  const handleSaveTags = useCallback(async () => {
    if (!document) return;
    setTagsSaving(true);
    try {
      await documentsApi.updateTags(document.id, editingTags, document.category || undefined);
      setDocument((prev) => prev ? { ...prev, tags: editingTags } : prev);
      setTagsChanged(false);
      message.success('标签更新成功');
    } catch {
      message.error('更新标签失败');
    } finally {
      setTagsSaving(false);
    }
  }, [document, editingTags]);

  const handleTagsChange = useCallback((values: string[]) => {
    setEditingTags(values);
    setTagsChanged(true);
  }, []);

  const copyShareUrl = useCallback(() => {
    navigator.clipboard.writeText(shareUrl).then(
      () => message.success('链接已复制到剪贴板'),
      () => message.error('复制失败'),
    );
  }, [shareUrl]);

  if (loading) {
    return (
      <div className="page-container">
        <LoadingSkeleton type="detail" />
      </div>
    );
  }

  if (!document) {
    return (
      <div className="page-container">
        <EmptyState
          title="文档不存在"
          description="未找到该文档，可能已被删除"
          action={
            <Button onClick={() => navigate('/documents')}>
              <ArrowLeftOutlined /> 返回文档列表
            </Button>
          }
        />
      </div>
    );
  }

  const ocrConfig = OCR_STATUS_CONFIG[document.ocr_status] || OCR_STATUS_CONFIG.pending;

  return (
    <div className="page-container">
      <PageHeader
        title={document.filename}
        breadcrumb={[
          { title: '文档管理', path: '/documents' },
          { title: document.filename },
        ]}
        extra={
          <Button onClick={() => navigate('/documents')}>
            <ArrowLeftOutlined /> 返回列表
          </Button>
        }
      />

      <Row gutter={24}>
        {/* Left: Document Preview */}
        <Col xs={24} lg={14}>
          <Card
            style={{ borderRadius: 12, minHeight: 480, marginBottom: 16 }}
            styles={{ body: { display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: 440 } }}
          >
            {document.mime_type?.includes('image') ? (
              // For images, try to display inline
              <div style={{ textAlign: 'center', width: '100%' }}>
                <img
                  src={`/api/v1/documents/${document.id}/download`}
                  alt={document.filename}
                  style={{ maxWidth: '100%', maxHeight: 400, objectFit: 'contain', borderRadius: 8 }}
                  onError={(e) => {
                    // Fallback to placeholder if image fails to load
                    const target = e.currentTarget;
                    target.style.display = 'none';
                    const fallback = window.document.getElementById('preview-fallback');
                    if (fallback) fallback.style.display = 'block';
                  }}
                />
                <div id="preview-fallback" style={{ display: 'none' }}>
                  {getPreviewIcon(document.mime_type)}
                  <Title level={5} style={{ marginTop: 16 }}>{document.filename}</Title>
                </div>
              </div>
            ) : (
              // Placeholder for non-image files
              <div style={{ textAlign: 'center' }}>
                {getPreviewIcon(document.mime_type)}
                <Title level={4} style={{ marginTop: 16, marginBottom: 4 }}>{document.filename}</Title>
                <Text type="secondary">
                  {document.mime_type?.includes('pdf') ? 'PDF 文档' : '文档文件'} · {formatFileSize(document.file_size)}
                </Text>
                <div style={{ marginTop: 24 }}>
                  <Space>
                    <Button type="primary" icon={<DownloadOutlined />} onClick={handleDownload} size="large">
                      下载查看
                    </Button>
                    <Button icon={<ScanOutlined />} onClick={handleTriggerOcr} loading={ocrLoading}>
                      识别文字
                    </Button>
                  </Space>
                </div>
              </div>
            )}
          </Card>

          {/* OCR Text Section */}
          {document.ocr_status === 'completed' && document.ocr_text && (
            <Card style={{ borderRadius: 12, marginBottom: 16 }}>
              <Collapse
                items={[
                  {
                    key: 'ocr-text',
                    label: (
                      <Space>
                        <CheckCircleOutlined style={{ color: '#52c41a' }} />
                        <span>OCR 识别结果</span>
                        <Tag color="success">已完成</Tag>
                      </Space>
                    ),
                    children: (
                      <Paragraph
                        style={{
                          whiteSpace: 'pre-wrap',
                          maxHeight: 400,
                          overflow: 'auto',
                          background: '#fafafa',
                          padding: 16,
                          borderRadius: 6,
                          margin: 0,
                        }}
                      >
                        {document.ocr_text}
                      </Paragraph>
                    ),
                  },
                ]}
              />
            </Card>
          )}

          {document.ocr_status === 'failed' && (
            <Alert
              message="OCR 识别失败"
              description="文字识别未能成功完成，请重试或检查文档是否清晰可读。"
              type="warning"
              showIcon
              action={
                <Button size="small" onClick={handleTriggerOcr} loading={ocrLoading}>
                  重试
                </Button>
              }
              style={{ marginBottom: 16 }}
            />
          )}

          {document.ocr_status === 'processing' && (
            <Card style={{ borderRadius: 12, marginBottom: 16 }}>
              <div style={{ textAlign: 'center', padding: '24px 0' }}>
                <Spin size="large" />
                <div style={{ marginTop: 12 }}>
                  <Text type="secondary">OCR 识别进行中，请稍候...</Text>
                </div>
              </div>
            </Card>
          )}
        </Col>

        {/* Right: Document Info Panel */}
        <Col xs={24} lg={10}>
          <Card style={{ borderRadius: 12, marginBottom: 16 }} title="文档信息">
            <Descriptions column={1} size="small" bordered>
              <Descriptions.Item label="文件名">
                <Text strong>{document.filename}</Text>
              </Descriptions.Item>
              <Descriptions.Item label="文件大小">
                {formatFileSize(document.file_size)}
              </Descriptions.Item>
              <Descriptions.Item label="页数">
                {document.page_count ? `${document.page_count} 页` : <Text type="secondary">未知</Text>}
              </Descriptions.Item>
              <Descriptions.Item label="类别">
                {document.category ? (
                  <Tag color="purple">{document.category}</Tag>
                ) : (
                  <Text type="secondary">未分类</Text>
                )}
              </Descriptions.Item>
              <Descriptions.Item label="OCR 状态">
                <Tag icon={ocrConfig.icon} color={ocrConfig.color}>
                  {ocrConfig.text}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="文件类型">
                <Tag>{document.mime_type || '未知'}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="创建时间">
                {formatDate(document.created_at)}
              </Descriptions.Item>
              <Descriptions.Item label="分享状态">
                {document.is_shared ? (
                  <Tag color="blue">已分享</Tag>
                ) : (
                  <Tag>未分享</Tag>
                )}
              </Descriptions.Item>
            </Descriptions>

            {/* Tag Editor */}
            <div style={{ marginTop: 20 }}>
              <Text strong style={{ display: 'block', marginBottom: 8 }}>标签</Text>
              <Space direction="vertical" style={{ width: '100%' }}>
                <Select
                  mode="tags"
                  value={editingTags}
                  onChange={handleTagsChange}
                  placeholder="添加标签..."
                  style={{ width: '100%' }}
                  maxTagCount={10}
                />
                {tagsChanged && (
                  <Button
                    type="primary"
                    size="small"
                    onClick={handleSaveTags}
                    loading={tagsSaving}
                  >
                    保存标签
                  </Button>
                )}
              </Space>
            </div>

            {/* Action Buttons */}
            <div style={{ marginTop: 20 }}>
              <Text strong style={{ display: 'block', marginBottom: 12 }}>操作</Text>
              <Space direction="vertical" style={{ width: '100%' }}>
                <Button
                  icon={<DownloadOutlined />}
                  onClick={handleDownload}
                  block
                  type="primary"
                >
                  下载文档
                </Button>
                <Button
                  icon={<ScanOutlined />}
                  onClick={handleTriggerOcr}
                  loading={ocrLoading}
                  block
                  disabled={document.ocr_status === 'processing'}
                >
                  {document.ocr_status === 'completed' ? '重新 OCR 识别' : '触发 OCR 识别'}
                </Button>
                <Button
                  icon={<ShareAltOutlined />}
                  onClick={handleShare}
                  loading={shareLoading}
                  block
                >
                  分享文档
                </Button>
              </Space>
            </div>
          </Card>
        </Col>
      </Row>

      {/* Share Modal */}
      <Modal
        title="分享文档"
        open={shareModalOpen}
        onCancel={() => setShareModalOpen(false)}
        footer={[
          <Button key="close" onClick={() => setShareModalOpen(false)}>
            关闭
          </Button>,
        ]}
      >
        <div style={{ marginBottom: 16 }}>
          <Text type="secondary">分享链接（24小时有效）：</Text>
        </div>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            padding: '8px 12px',
            background: '#fafafa',
            borderRadius: 6,
            border: '1px solid #f0f0f0',
            wordBreak: 'break-all',
          }}
        >
          <Text style={{ flex: 1, fontSize: 13 }}>{shareUrl}</Text>
          <Button
            type="text"
            icon={<CopyOutlined />}
            onClick={copyShareUrl}
            size="small"
          />
        </div>
      </Modal>
    </div>
  );
};

export default DocumentDetailPage;
