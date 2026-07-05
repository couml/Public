import React, { useEffect } from 'react';
import { Select, Space } from 'antd';
import { PrinterOutlined } from '@ant-design/icons';
import { useDeviceStore } from '@/store/deviceStore';
import StatusBadge from '@/components/StatusBadge';
import type { Printer } from '@/types/device';

interface PrinterSelectorProps {
  value?: string;
  onChange?: (printerId: string) => void;
  filterOnline?: boolean;
}

const PrinterSelector: React.FC<PrinterSelectorProps> = ({ value, onChange, filterOnline = false }) => {
  const { devices, isLoading, fetchDevices } = useDeviceStore();

  useEffect(() => {
    fetchDevices();
  }, [fetchDevices]);

  const filteredDevices = filterOnline ? devices.filter((d) => d.status === 'online') : devices;

  const renderOption = (printer: Printer) => ({
    value: printer.id,
    label: (
      <Space>
        <PrinterOutlined />
        <span>{printer.name}</span>
        <StatusBadge status={printer.status} size="small" />
        {printer.location && (
          <span style={{ color: '#8c8c8c', fontSize: 12 }}>{printer.location}</span>
        )}
      </Space>
    ),
  });

  return (
    <Select
      value={value}
      onChange={onChange}
      loading={isLoading}
      placeholder="选择打印机"
      style={{ minWidth: 240 }}
      options={filteredDevices.map(renderOption)}
      showSearch
      filterOption={(input, option) => {
        if (!option?.label) return false;
        const label = option.label as React.ReactElement;
        const children = label.props?.children;
        if (!children) return false;
        const text = Array.isArray(children)
          ? children.filter((c: unknown) => typeof c === 'string').join('')
          : String(children);
        return text.toLowerCase().includes(input.toLowerCase());
      }}
      notFoundContent="没有找到打印机"
    />
  );
};

export default PrinterSelector;
