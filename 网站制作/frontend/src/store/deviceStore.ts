import { create } from 'zustand';
import type { Printer, DeviceStatusUpdate } from '@/types/device';
import { devicesApi } from '@/api/devices';

interface DeviceState {
  devices: Printer[];
  selectedDevice: Printer | null;
  deviceStatuses: Record<string, DeviceStatusUpdate>;
  totalDevices: number;
  isLoading: boolean;
  fetchDevices: (params?: { brand?: string; status?: string; search?: string; page?: number }) => Promise<void>;
  fetchDevice: (id: string) => Promise<void>;
  updateStatus: (status: DeviceStatusUpdate) => void;
  setSelectedDevice: (device: Printer | null) => void;
}

export const useDeviceStore = create<DeviceState>((set, get) => ({
  devices: [],
  selectedDevice: null,
  deviceStatuses: {},
  totalDevices: 0,
  isLoading: false,

  fetchDevices: async (params) => {
    set({ isLoading: true });
    try {
      const res = await devicesApi.list(params);
      set({ devices: res.items, totalDevices: res.total, isLoading: false });
    } catch {
      set({ isLoading: false });
    }
  },

  fetchDevice: async (id) => {
    try {
      const device = await devicesApi.getById(id);
      set({ selectedDevice: device });
    } catch (error) {
      console.error('Failed to fetch device:', error);
    }
  },

  updateStatus: (status) => {
    set((state) => ({
      deviceStatuses: { ...state.deviceStatuses, [status.id]: status },
      devices: state.devices.map((d) =>
        d.id === status.id
          ? { ...d, status: status.status, toner_level: status.toner_level, paper_level: status.paper_level }
          : d
      ),
    }));
  },

  setSelectedDevice: (device) => set({ selectedDevice: device }),
}));
