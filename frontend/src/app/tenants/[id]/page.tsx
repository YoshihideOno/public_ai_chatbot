import { TenantForm } from '@/components/tenants/TenantForm';
import { AdminRoute } from '@/components/auth/ProtectedRoute';

interface TenantDetailPageProps {
  params: {
    id: string;
  };
}

export default function TenantDetailPage({ params }: TenantDetailPageProps) {
  return (
    <AdminRoute>
      <TenantForm tenantId={params.id} mode="view" />
    </AdminRoute>
  );
}
