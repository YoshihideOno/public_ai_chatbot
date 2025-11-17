import { UserForm } from '@/components/users/UserForm';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

export default function NewUserPage() {
  return (
    <ProtectedRoute>
      <UserForm mode="create" />
    </ProtectedRoute>
  );
}
