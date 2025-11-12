import { UserForm } from '@/components/users/UserForm';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

interface EditUserPageProps {
  params: {
    id: string;
  };
}

export default function EditUserPage({ params }: EditUserPageProps) {
  return (
    <ProtectedRoute>
      <UserForm userId={params.id} mode="edit" />
    </ProtectedRoute>
  );
}
