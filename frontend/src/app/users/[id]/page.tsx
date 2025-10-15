import { UserForm } from '@/components/users/UserForm';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

interface UserDetailPageProps {
  params: {
    id: string;
  };
}

export default function UserDetailPage({ params }: UserDetailPageProps) {
  return (
    <ProtectedRoute>
      <UserForm userId={parseInt(params.id)} mode="view" />
    </ProtectedRoute>
  );
}
