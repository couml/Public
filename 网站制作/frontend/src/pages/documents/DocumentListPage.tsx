import React, { useEffect, useState, useMemo, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Row,
  Col,
  Card,
  Pagination,
  Select,
  Tag,
  Button,
  Typography,
  Space,
  Dropdown,
  Modal,
  message,
  Input,
  Tooltip,
} from 'antd';
import {
  FilePdfOutlined,
  FileImageOutlined,
  FileTextOutlined,
  UploadOutlined,
  DownloadOutlined,
  ShareAltOutlined,
  DeleteOutlined,
  ScanOutlined,
  EyeOutlined,
  MoreOutlined,
  TagsOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  SyncOutlined,
  CloseCircleOutlined,
} from '@ant-design/icons';
import PageHeader from '@/components/PageHeader';
import SearchBar from '@/components/SearchBar';
import EmptyState from '@/components/EmptyState';
import LoadingSkeleton from '@/components/LoadingSkeleton';
import { documentsApi } from '@/api/documents';
import { formatFileSize, formatRelativeTime, formatDate } from '@/utils/format';
import type { ScanDocument } from '@/types/document';

const { Text, Title, Paragraph } = Typography;

const CATEGORY_OPTIONS = [
  { label: '全部分类', value: '' },
  { label: '合同', value: 'Contract' },
  { label: '报告', value: 'Report' },
  { label: '发票', value: 'Invoice' },
  { label: '其他', value: 'Other' },
];

const COMMON_TAGS = ['重要', '已归档', '待审核', '财务', '行政', '技术', '合同', '报告'];

const OCR_STATUS_CONFIG: Record<string, { color: string; icon: React.ReactNode; text: string }> = {
  pending: { color: 'default', icon: <ClockCircleOutlined />, text: '待识别' },
  processing: { color: 'processing', icon: <SyncOutlined spin />, text: '识别中' },
  completed: { color: 'success', icon: <CheckCircleOutlined />, text: '已识别' },
  failed: { color: 'error', icon: <CloseCircleOutlined />, text: '识别失败' },
};

function getFileIcon(mimeType: string | null) {
  if (!mimeType) return <FileTextOutlined style={{ fontSize: 40, color: '#8c8c8c' }} />;
  if (mimeType.includes('pdf')) {
    return <FilePdfOutlined style={{ fontSize: 40, color: '#ff4d4f' }} />;
  }
  if (mimeType.includes('image')) {
    return <FileImageOutlined style={{ fontSize: 40, color: '#1677ff' }} />;
  }
  return <FileTextOutlined style={{ fontSize: 40, color: '#8c8c8c' }} />;
}

const DocumentListPage: React.FC = () => {
  const navigate = useNavigate();
  const [documents, setDocuments] = useState<ScanDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const pageSize = 12;

  const fetchDocuments = useCallback(async () => {
    setLoading(true);
    try {
      const data = await documentsApi.list({
        category: category || undefined,
        page,
        page_size: pageSize,
      });
      setDocuments(data.items);
      setTotal(data.total);
    } catch (error) {
      console.error('Failed to fetch documents:', error);
      setDocuments([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [category, page]);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  // Client-side filtering for search and tags
  const filteredDocuments = useMemo(() => {
    let result = documents;
    if (search.trim()) {
      const lower = search.toLowerCase();
      result = result.filter(
        (d) =>
          d.filename.toLowerCase().includes(lower) ||
          d.tags.some((t) => t.toLowerCase().includes(lower)),
      );
    }
    if (selectedTags.length > 0) {
      result = result.filter((d) => selectedTags.some((t) => d.tags.includes(t)));
    }
    return result;
  }, [documents, search, selectedTags]);

  const handleSearch = useCallback((value: string) => {
    setSearch(value);
    setPage(1);
  }, []);

  const handleCategoryChange = useCallback((value: string) => {
    setCategory(value);
    setPage(1);
  }, []);

  const handleDelete = useCallback(
    async (doc: ScanDocument) => {
      Modal.confirm({
        title: '确认删除',
        content: `确定要删除文档 "${doc.filename}" 吗？此操作不可撤销。`,
        okText: '删除',
        okType: 'danger',
        cancelText: '取消',
        onOk: async () => {
          message.success('文档已删除（示例）');
          fetchDocuments();
        },
      });
    },
    [fetchDocuments],
  );

  const handleTriggerOcr = useCallback(
    async (docId: string) => {
      try {
        await documentsApi.triggerOcr(docId);
        message.success('OCR 识别任务已触发');
        fetchDocuments();
      } catch {
        message.error('触发 OCR 失败');
      }
    },
    [fetchDocuments],
  );

  const handleShare = useCallback(async (doc: ScanDocument) => {
    try {
      const result = await documentsApi.share(doc.id);
      const shareToken = result?.share_token || doc.share_token;
      const shareUrl = `${window.location.origin}/documents/shared/${shareToken}`;
      Modal.info({
        title: '分享链接',
        content: (
          <div>
            <Paragraph copyable={{ text: shareUrl }} style={{ marginBottom: 8 }}>
              {shareUrl}
            </Paragraph>
            <Text type="secondary">链接有效期为 24 小时</Text>
          </div>
        ),
        okText: '关闭',
      });
    } catch {
      message.error('生成分享链接失败');
    }
  }, []);

  const handleDownload = useCallback((doc: ScanDocument) => {
    const url = documentsApi.getDownloadUrl(doc.id);
    window.open(url, '_blank');
    message.success('开始下载...');
  }, []);

  const getDropdownItems = (doc: ScanDocument) => ({
    items: [
      {
        key: 'preview',
        icon: <EyeOutlined />,
        label: '预览',
        onClick: () => navigate(`/documents/${doc.id}`),
      },
      {
        key: 'download',
        icon: <DownloadOutlined />,
        label: '下载',
        onClick: () => handleDownload(doc),
      },
      {
        key: 'share',
        icon: <ShareAltOutlined />,
        label: '分享',
        onClick: () => handleShare(doc),
      },
      {
        key: 'ocr',
        icon: <ScanOutlined />,
        label: '触发 OCR',
        disabled: doc.ocr_status === 'processing',
        onClick: () => handleTriggerOcr(doc.id),
      },
      { type: 'divider' as const },
      {
        key: 'delete',
        icon: <DeleteOutlined />,
        label: '删除',
        danger: true,
        onClick: () => handleDelete(doc),
      },
    ],
  });

  return (
    <div className="page-container">
      <PageHeader
        title="电子文档管理"
        extra={
          <Button type="primary" icon={<UploadOutlined />} onClick={() => setUploadModalOpen(true)}>
            上传文档
          </Button>
        }
      />

      {/* Filter Bar */}
      <Card style={{ marginBottom: 24 }}>
        <Space wrap size="middle">
          <SearchBar onSearch={handleSearch} placeholder="搜索文件名或标签..." />

          <Select
            value={category || undefined}
            onChange={handleCategoryChange}
            style={{ width: 120 }}
            options={CATEGORY_OPTIONS.map((o) => ({ label: o.label, value: o.value || undefined }))}
          />

          <Select
            mode="multiple"
            value={selectedTags.length > 0 ? selectedTags : undefined}
            onChange={setSelectedTags}
            placeholder="标签筛选"
            style={{ minWidth: 180 }}
            maxTagCount={3}
            options={COMMON_TAGS.map((t) => ({ label: t, value: t }))}
            allowClear
          />
        </Space>
      </Card>

      {/* Document Grid */}
      {loading ? (
        <Row gutter={[16, 16]}>
          {Array.from({ length: 8 }).map((_, i) => (
            <Col span={6} key={i}>
              <LoadingSkeleton type="card" />
            </Col>
          ))}
        </Row>
      ) : filteredDocuments.length === 0 ? (
        <EmptyState
          title="暂无文档"
          description={documents.length === 0 ? '尚未上传任何文档' : '没有匹配的文档，请调整筛选条件'}
          action={
            documents.length === 0 ? (
              <Button type="primary" icon={<UploadOutlined />} onClick={() => setUploadModalOpen(true)}>
                上传文档
              </Button>
            ) : undefined
          }
        />
      ) : (
        <>
          <Row gutter={[16, 16]}>
            {filteredDocuments.map((doc) => {
              const ocrConfig = OCR_STATUS_CONFIG[doc.ocr_status];
              return (
                <Col span={6} key={doc.id}>
                  <Card
                    hoverable
                    style={{ height: '100%', borderRadius: 8 }}
                    onClick={() => navigate(`/documents/${doc.id}`)}
                    actions={[
                      <Dropdown menu={getDropdownItems(doc)} trigger={['click']} key="more">
                        <Button
                          type="text"
                          icon={<MoreOutlined />}
                          onClick={(e) => e.stopPropagation()}
                        >
                          操作
                        </Button>
                      </Dropdown>,
                    ]}
                  >
                    {/* Thumbnail */}
                    <div
                      style={{
                        width: '100%',
                        height: 120,
                        borderRadius: 6,
                        background: '#fafafa',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        marginBottom: 12,
                        border: '1px solid #f0f0f0',
                      }}
                    >
                      {getFileIcon(doc.mime_type)}
                    </div>

                    {/* Filename */}
                    <Tooltip title={doc.filename}>
                      <div
                        style={{
                          fontWeight: 600,
                          fontSize: 14,
                          marginBottom: 8,
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {doc.filename}
                      </div>
                    </Tooltip>

                    {/* Meta info */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                      {doc.page_count ? (
                        <Tag icon={<FileTextOutlined />}>{doc.page_count} 页</Tag>
                      ) : (
                        <Tag>{formatFileSize(doc.file_size)}</Tag>
                      )}
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {formatRelativeTime(doc.created_at)}
                      </Text>
                    </div>

                    {/* Category */}
                    {doc.category && (
                      <Tag color="purple" style={{ marginBottom: 6 }}>
                        {doc.category}
                      </Tag>
                    )}

                    {/* Tags */}
                    {doc.tags && doc.tags.length > 0 && (
                      <div style={{ marginBottom: 8, display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                        {doc.tags.slice(0, 3).map((t) => (
                          <Tag key={t} style={{ fontSize: 11 }}>{t}</Tag>
                        ))}
                        {doc.tags.length > 3 && (
                          <Tag style={{ fontSize: 11 }}>+{doc.tags.length - 3}</Tag>
                        )}
                      </div>
                    )}

                    {/* OCR Status */}
                    <Tag
                      icon={ocrConfig?.icon}
                      color={ocrConfig?.color}
                      style={{ fontSize: 12 }}
                    >
                      {ocrConfig?.text || doc.ocr_status}
                    </Tag>
                  </Card>
                </Col>
              );
            })}
          </Row>

          {total > pageSize && (
            <div style={{ marginTop: 24, textAlign: 'center' }}>
              <Pagination
                current={page}
                pageSize={pageSize}
                total={total}
                onChange={(p) => setPage(p)}
                showSizeChanger={false}
                showTotal={(t) => `共 ${t} 个文档`}
              />
            </div>
          )}
        </>
      )}

      {/* Upload Modal (placeholder) */}
      <Modal
        title="上传文档"
        open={uploadModalOpen}
        onCancel={() => setUploadModalOpen(false)}
        footer={null}
        width={520}
      >
        <EmptyState
          title="文档上传功能"
          description="上传功能将在后续版本中实现。您可以在此拖拽或选择文件进行上传。"
          icon={<UploadOutlined style={{ fontSize: 48, color: '#bfbfbf' }} />}
        />
      </Modal>
    </div>
  );
};

export default DocumentListPage;
