import { TenantForm } from '@/components/tenants/TenantForm';
import { AdminRoute } from '@/components/auth/ProtectedRoute';

interface EditTenantPageProps {
  params: {
    id: string;
  };
}

export default function EditTenantPage({ params }: EditTenantPageProps) {
  return (
    <AdminRoute>
      <TenantForm tenantId={params.id} mode="edit" />
    </AdminRoute>
  );
}
