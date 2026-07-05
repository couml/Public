import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider, Spin } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { theme } from '@/styles/theme';
import AuthGuard from '@/components/AuthGuard';

// Lazy-loaded page imports
const LoginPage = lazy(() => import('@/pages/auth/LoginPage'));
const RegisterPage = lazy(() => import('@/pages/auth/RegisterPage'));

const DashboardLayout = lazy(() => import('@/layouts/DashboardLayout'));
const DashboardPage = lazy(() => import('@/pages/dashboard/DashboardPage'));
const DeviceListPage = lazy(() => import('@/pages/devices/DeviceListPage'));
const DeviceDetailPage = lazy(() => import('@/pages/devices/DeviceDetailPage'));
const DiagnosisPage = lazy(() => import('@/pages/diagnosis/DiagnosisPage'));
const DiagnosisReportPage = lazy(() => import('@/pages/diagnosis/DiagnosisReportPage'));
const PrintPage = lazy(() => import('@/pages/print/PrintPage'));
const PrintHistoryPage = lazy(() => import('@/pages/print/PrintHistoryPage'));
const DriverListPage = lazy(() => import('@/pages/drivers/DriverListPage'));
const DriverDetailPage = lazy(() => import('@/pages/drivers/DriverDetailPage'));
const DocumentListPage = lazy(() => import('@/pages/documents/DocumentListPage'));
const DocumentDetailPage = lazy(() => import('@/pages/documents/DocumentDetailPage'));

const AdminLayout = lazy(() => import('@/layouts/AdminLayout'));
const AdminDashboardPage = lazy(() => import('@/pages/admin/AdminDashboardPage'));
const AdminPrinterPage = lazy(() => import('@/pages/admin/AdminPrinterPage'));
const AdminDriverPage = lazy(() => import('@/pages/admin/AdminDriverPage'));
const AdminUserPage = lazy(() => import('@/pages/admin/AdminUserPage'));
const AdminLogPage = lazy(() => import('@/pages/admin/AdminLogPage'));

const PageLoading: React.FC = () => (
  <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
    <Spin size="large" />
  </div>
);

const App: React.FC = () => {
  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        token: {
          colorPrimary: theme.primaryColor,
          borderRadius: theme.borderRadius,
          colorBgContainer: theme.colorBgContainer,
          fontFamily: theme.fontFamily,
        },
      }}
    >
      <BrowserRouter basename={import.meta.env.BASE_URL || '/'}>
        <Suspense fallback={<PageLoading />}>
          <Routes>
            {/* Public routes */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />

            {/* Authenticated routes */}
            <Route element={<AuthGuard />}>
              <Route element={<DashboardLayout />}>
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route path="/dashboard" element={<DashboardPage />} />
                <Route path="/devices" element={<DeviceListPage />} />
                <Route path="/devices/:id" element={<DeviceDetailPage />} />
                <Route path="/diagnosis" element={<DiagnosisPage />} />
                <Route path="/diagnosis/:id" element={<DiagnosisReportPage />} />
                <Route path="/print" element={<PrintPage />} />
                <Route path="/print/history" element={<PrintHistoryPage />} />
                <Route path="/drivers" element={<DriverListPage />} />
                <Route path="/drivers/:brand/:model" element={<DriverDetailPage />} />
                <Route path="/documents" element={<DocumentListPage />} />
                <Route path="/documents/:id" element={<DocumentDetailPage />} />
              </Route>
            </Route>

            {/* Admin routes */}
            <Route element={<AuthGuard roles={['admin', 'it_staff']} />}>
              <Route element={<AdminLayout />}>
                <Route path="/admin" element={<AdminDashboardPage />} />
                <Route path="/admin/printers" element={<AdminPrinterPage />} />
                <Route path="/admin/drivers" element={<AdminDriverPage />} />
                <Route path="/admin/users" element={<AdminUserPage />} />
                <Route path="/admin/logs" element={<AdminLogPage />} />
              </Route>
            </Route>

            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </Suspense>
      </BrowserRouter>
    </ConfigProvider>
  );
};

export default App;
