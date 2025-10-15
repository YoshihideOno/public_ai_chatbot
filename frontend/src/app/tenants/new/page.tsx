import { TenantForm } from '@/components/tenants/TenantForm';
import { AdminRoute } from '@/components/auth/ProtectedRoute';

export default function NewTenantPage() {
  return (
    <AdminRoute>
      <TenantForm mode="create" />
    </AdminRoute>
  );
}
