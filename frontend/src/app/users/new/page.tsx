import { UserForm } from '@/components/users/UserForm';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

interface NewUserPageProps {
  params: {
    id?: string;
  };
}

export default function NewUserPage({ params }: NewUserPageProps) {
  return (
    <ProtectedRoute>
      <UserForm mode="create" />
    </ProtectedRoute>
  );
}
