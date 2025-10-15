import { TenantsList } from '@/components/tenants/TenantsList';
import { AdminRoute } from '@/components/auth/ProtectedRoute';

export default function TenantsPage() {
  return (
    <AdminRoute>
      <TenantsList />
    </AdminRoute>
  );
}
